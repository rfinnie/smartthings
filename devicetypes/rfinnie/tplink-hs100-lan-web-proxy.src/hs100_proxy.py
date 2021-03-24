#!/usr/bin/env python3

# hs100_proxy - TP-LINK Smart Plug HS100 series LAN web proxy
# Copyright (C) 2016-2021 Ryan Finnie
# SPDX-License-Identifier: MPL-2.0

import http.server
import json
import logging
import socket
import struct
import urllib.parse


class HS100Handler(http.server.BaseHTTPRequestHandler):
    post_body = None
    config = None

    def decode(self, input):
        input_len = len(input)
        state = 0xAB
        output = bytearray(input_len)
        for pos in range(input_len):
            i = input[pos]
            output[pos] = i ^ state
            state = i
        return bytes(output)

    def encode(self, input):
        input_len = len(input)
        state = 0xAB
        output = bytearray(input_len)
        for pos in range(input_len):
            state = input[pos] ^ state
            output[pos] = state
        return bytes(output)

    def send_command(self, host, port, command):
        sock = socket.socket()
        sock.connect((host, port))

        sock.send(struct.pack("!l", len(command)) + self.encode(command))

        result = self.decode(sock.recv(8192)[4:])
        sock.close()

        return result

    def log_request(self, code="-", size="-", user_agent="-", extra="-"):
        if self.headers.get("User-Agent"):
            user_agent = self.headers.get("User-Agent")
        if self.post_body:
            extra = self.post_body.decode("UTF-8")
        extra = extra.replace("\r", "").replace("\n", "")
        if len(extra) > 100:
            extra = extra[0:97] + "..."
        self.log_message(
            '"{}" {} {} "-" "{}" "{}"'.format(
                self.requestline, str(code), str(size), user_agent, extra
            )
        )

    def do_request(self):
        try:
            path = urllib.parse.urlparse(self.path)

            if self.command == "POST":
                if not self.headers.get("Content-Length"):
                    return self.send_error(400)
                if path.path == "/command":
                    return self.do_command()
                else:
                    return self.send_error(404)
            elif self.command == "GET":
                if path.path == "/":
                    return self.do_index()
                else:
                    return self.send_error(404)
            else:
                return self.send_error(400)
        except Exception:
            logging.exception("Unknown error")
            self.send_error(500)

    def do_POST(self):
        return self.do_request()

    def do_GET(self):
        return self.do_request()

    def do_command(self):
        command_data = self.rfile.read(int(self.headers.get("Content-Length")))
        self.post_body = command_data
        result = self.send_command(
            self.config.hs100_addr, self.config.hs100_port, command_data
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(result))
        self.end_headers()
        self.wfile.write(result)

    def result_status_text(self, r):
        output = "SERVER INFORMATION\n"
        output += "    {:16}: {}\n".format("Date", self.date_time_string())
        output += "    {:16}: {}:{}\n".format(
            "Device", self.config.hs100_addr, self.config.hs100_port
        )
        output += "    {:16}: {}:{}\n".format(
            "Local", self.config.local_addr, self.config.local_port
        )
        output += "    {:16}: {}:{}\n".format(
            "Remote", self.client_address[0], self.client_address[1]
        )
        output += "    {:16}: {}\n".format("User agent", self.headers.get("User-Agent"))

        output += "\nDEVICE STATUS\n"
        for (k, v) in sorted(r["system"]["get_sysinfo"].items()):
            output += "    {:16}: {}\n".format(k, v)

        output += "\nEXAMPLES\n\n"

        def example_curl(command):
            return "    {}\n\n".format(
                "curl -s --data-binary '{}' -H \"Content-type: application/json\" http://{}/command | json_pp".format(
                    json.dumps(command), self.headers.get("Host")
                )
            )

        output += "Device status:\n"
        output += example_curl({"system": {"get_sysinfo": {"state": None}}})

        output += "Turn on outlet:\n"
        output += example_curl({"system": {"set_relay_state": {"state": 1}}})

        output += "Turn off outlet:\n"
        output += example_curl({"system": {"set_relay_state": {"state": 0}}})

        return output

    def do_index(self):
        command_data = json.dumps({"system": {"get_sysinfo": {"state": None}}}).encode(
            "UTF-8"
        )
        result = self.send_command(
            self.config.hs100_addr, self.config.hs100_port, command_data
        )
        result_d = json.loads(result.decode("UTF-8"))
        output = self.result_status_text(result_d)
        output_bytes = output.encode("UTF-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", len(output_bytes))
        self.end_headers()
        self.wfile.write(output_bytes)


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="hs100_proxy - TP-LINK Smart Plug HS100 series LAN web proxy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--debug", action="store_true", help="Print extra debugging")
    parser.add_argument(
        "--local-port", "-l", type=int, default=8362, help="local port for web server"
    )
    parser.add_argument(
        "--local-addr", type=str, default="0.0.0.0", help="local address for web server"
    )
    parser.add_argument(
        "--hs100-port",
        "-p",
        type=int,
        default=9999,
        help="port for HS100 series device",
    )
    parser.add_argument(
        "hs100_addr", type=str, help="address/hostname for HS100 series device"
    )
    return parser.parse_args()


if __name__ == "__main__":
    config = parse_args()

    if config.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logging.basicConfig(level=logging_level)
    server_class = http.server.HTTPServer
    httpd = server_class((config.local_addr, config.local_port), HS100Handler)
    httpd.RequestHandlerClass.config = config
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
