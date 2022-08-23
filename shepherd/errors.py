

from .utils.cmdline_controller import CommandlineError
from .inventory import InventoryError, InventoryFileMissing, NoHostsError


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


class NetworkError(RuntimeError):
    pass
