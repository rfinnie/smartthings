#!/usr/bin/python

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

import BaseHTTPServer
import socket


class HS100Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    post_body = None
    config = None

    def decode(self, a):
        code = 0xab
        b = ''
        for i in a:
            b += chr(ord(i) ^ code)
            code = ord(i)
        return b

    def encode(self, a):
        code = 0xab
        b = ''
        for i in a:
            b += chr((ord(i) ^ code))
            code = (ord(b[len(b) - 1]))
        return b

    def send_command(self, host, port, command):
        sock = socket.socket()
        sock.connect((host, port))

        sock.send('\x00\x00\x00\x23' + self.encode(command))

        result = self.decode(sock.recv(8192)[4:])
        sock.close()

        return result

    def log_request(self, code='-', size='-', user_agent='-', extra='-'):
        if self.headers.getheader('User-Agent'):
            user_agent = self.headers.getheader('User-Agent')
        if self.post_body:
            extra = self.post_body
        extra = extra.replace('\r', '').replace('\n', '')
        if len(extra) > 100:
            extra = extra[0:97] + '...'
        self.log_message(
            '"%s" %s %s "-" "%s" "%s"',
            self.requestline,
            str(code),
            str(size),
            user_agent,
            extra,
        )

    def error_500(self, message):
        self.send_response(500)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message)

    def do_POST(self):
        if not self.headers.getheader('Content-Length'):
            self.send_response(400)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write('Content-Length required.')
            return
        command_data = self.rfile.read(
            int(self.headers.getheader('Content-Length'))
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
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(result))
        self.end_headers()
        self.wfile.write(result)


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
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((config.local_addr, config.local_port), HS100Handler)
    httpd.RequestHandlerClass.config = config
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
