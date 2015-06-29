from __future__ import absolute_import

import exceptions

from .utils.cmdline_controller import CommandlineError


class AuthError(exceptions.RuntimeError):
    pass


class ActionError(CommandlineError):
    pass


class InstanceError(exceptions.RuntimeError):
    pass


class MissingInstanceError(InstanceError):
    pass


class ProviderError(exceptions.RuntimeError):
    pass
