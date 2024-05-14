import asyncio

from aiohttp import web


async def hello(request):

    return web.Response(text="Hello, CivTech project AAA!", content_type="text/plain")


async def main():

    app = web.Application()
    app.add_routes([web.get('/', hello)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print('Server started on http://0.0.0.0:8080/')
    await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
