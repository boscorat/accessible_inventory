class MasterGPOSError(Exception):
    pass


class MasterGKError(Exception):
    pass


class InventoryRemoveZeroError(Exception):
    pass


class InventoryRemoveExcessiveError(Exception):
    pass


class EntityDeleteHasInventoryError(Exception):
    pass
