"""
Entry point for pytoil, simply passes control uo
to the root click command.
"""


from pytoil.cli.root import main

main(_anyio_backend="asyncio")
