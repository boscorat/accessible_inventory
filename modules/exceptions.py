class MasterGPOSError(Exception):
    pass


class MasterGKError(Exception):
    pass


class InventoryRemoveZeroError(Exception):
    pass


class InventoryRemoveExcessiveError(Exception):
    pass


class ItemDeleteHasInventoryError(Exception):
    pass


class LocationDeleteHasInventoryError(Exception):
    pass
