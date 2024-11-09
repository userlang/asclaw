# 作者：langjunnan
# 开发时间：2025年7月23日

from enum import Enum


class TransportType(Enum):
    sse = 'sse'
    streamable_http = 'streamable_http'
    stdio = 'stdio'


class ServerType(Enum):
    remote = 'remote'
    local = 'local'


class CompileType(Enum):
    package = 'package'
    openapi = 'openapi'
