#!/usr/bin/env python3

# hs100_proxy - TP-LINK Smart Plug HS100 LAN web proxy
# Copyright (C) 2016 Ryan Finnie
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import http.server
import socket
import json
import struct


class HS100Handler(http.server.BaseHTTPRequestHandler):
    post_body = None
    config = None

    def decode(self, a):
        code = 0xab
        b = b''
        for i in a:
            b += bytes([i ^ code])
            code = i
        return b

    def encode(self, a):
        code = 0xab
        b = b''
        for i in a:
            code = i ^ code
            b += bytes([code])
        return b

    def send_command(self, host, port, command):
        sock = socket.socket()
        sock.connect((host, port))

        sock.send(struct.pack('!l', len(command)) + self.encode(command))

        result = self.decode(sock.recv(8192)[4:])
        sock.close()

        return result

    def log_request(self, code='-', size='-', user_agent='-', extra='-'):
        if self.headers.get('User-Agent'):
            user_agent = self.headers.get('User-Agent')
        if self.post_body:
            extra = self.post_body.decode('UTF-8')
        extra = extra.replace('\r', '').replace('\n', '')
        if len(extra) > 100:
            extra = extra[0:97] + '...'
        self.log_message('"{}" {} {} "-" "{}" "{}"'.format(
            self.requestline,
            str(code),
            str(size),
            user_agent,
            extra,
        ))

    def error_500(self, message):
        message_bytes = message.encode('UTF-8')
        self.send_response(500)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', len(message_bytes))
        self.end_headers()
        self.wfile.write(message_bytes)

    def do_POST(self):
        if not self.headers.get('Content-Length'):
            self.send_response(400)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write('Content-Length required.'.encode('UTF-8'))
            return
        command_data = self.rfile.read(
            int(self.headers.get('Content-Length'))
        )
        self.post_body = command_data
        try:
            result = self.send_command(
                self.config.hs100_addr,
                self.config.hs100_port,
                command_data
            )
        except socket.error as e:
            return self.error_500(str(e))
        except Exception as e:
            return self.error_500('Unknown exception: ' + str(e))
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(result))
        self.end_headers()
        self.wfile.write(result)

    def do_GET(self):
        command_data = json.dumps({
            'system': {
                'get_sysinfo': {
                    'state': None,
                }
            }
        }).encode('UTF-8')
        try:
            result = self.send_command(
                self.config.hs100_addr,
                self.config.hs100_port,
                command_data
            )
        except socket.error as e:
            return self.error_500(str(e))
        except Exception as e:
            return self.error_500('Unknown exception: ' + str(e))
        result_d = json.loads(result.decode('UTF-8'))
        output = ''
        for (k, v) in sorted(result_d['system']['get_sysinfo'].items()):
            output += '{}: {}\n'.format(k, v)
        output_bytes = output.encode('UTF-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', len(output_bytes))
        self.end_headers()
        self.wfile.write(output_bytes)


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description='hs100_proxy - TP-LINK Smart Plug HS100 LAN web proxy',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--local-port', '-l', type=int, default=8362,
        help='local port for web server',
    )
    parser.add_argument(
        '--local-addr', type=str, default='0.0.0.0',
        help='local address for web server',
    )
    parser.add_argument(
        '--hs100-port', '-p', type=int, default=9999,
        help='port for HS100 device',
    )
    parser.add_argument(
        'hs100_addr', type=str,
        help='address/hostname for HS100 device',
    )
    return parser.parse_args()


if __name__ == '__main__':
    config = parse_args()
    server_class = http.server.HTTPServer
    httpd = server_class((config.local_addr, config.local_port), HS100Handler)
    httpd.RequestHandlerClass.config = config
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
