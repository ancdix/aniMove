#!/usr/bin/env python3
"""Use the isolated MCP runtime: uvx --from mcp-for-blender python this_script.py ..."""
import argparse
import asyncio
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', choices=['get_scene_info', 'get_addon_status', 'execute_blender_code'])
    parser.add_argument('--code-file', type=Path)
    args = parser.parse_args()
    if args.tool == 'execute_blender_code' and args.code_file is None:
        parser.error('--code-file is required for execute_blender_code')
    params = StdioServerParameters(command='/home/ipsedesktop/.local/bin/uvx',
                                    args=['mcp-for-blender'], env=dict(os.environ, DISABLE_TELEMETRY='true'))
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            if args.tool == 'execute_blender_code':
                status = await session.call_tool('get_addon_status', {})
                if status.isError:
                    raise RuntimeError(str(status.content))
                print('ADDON', status.model_dump_json())
                scene = await session.call_tool('get_scene_info', {'user_prompt': 'Inspect the scene before the authorized motion-lab operation.'})
                if scene.isError:
                    raise RuntimeError(str(scene.content))
                print('BEFORE', scene.model_dump_json())
            arguments = {} if args.tool == 'get_addon_status' else {'user_prompt': 'Verify and inspect the AnyTop robot motion lab in Blender.'}
            if args.tool == 'execute_blender_code':
                arguments['code'] = args.code_file.read_text()
            result = await session.call_tool(args.tool, arguments)
            print('RESULT', result.model_dump_json())
            if result.isError:
                raise RuntimeError(str(result.content))


if __name__ == '__main__':
    asyncio.run(asyncio.wait_for(main(), timeout=60))
