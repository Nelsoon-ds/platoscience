import sys
from twisted.internet import asyncioreactor
try:
    asyncioreactor.install()
except Exception as e:
    # Reactor already installed, ignore
    pass
