from __future__ import absolute_import

from .utils.cmdline_controller import CommandlineError


class AuthError(RuntimeError):
    pass


class ActionError(CommandlineError):
    pass


class InstanceError(RuntimeError):
    pass


class MissingInstanceError(InstanceError):
    pass


class ProviderError(RuntimeError):
    pass
