
STORAGE_KEY = "schedular-payments"

class DataStore(dict):
    """
    This stores the following data for per-wallet persistence (the storage object comes from the wallet).
    
        "payments": [
            [
              Address,      # The address to pay to.
              Amount,       # Satoshis.
              DateLastPaid, # The date this was last paid, or None otherwise.
              When,         # Representation of how this is scheduled
              Count0,       # How many times this should be paid.  -1 = disabled, 0 = complete, > 100000 = countless
              CountN,       # How many payments remain of the original count.
              DateCreated,  # The date this schedular payment entry was created.
              Description,  # The description used to label the payments.
            ],
        ]
    """

    def __init__(self, storage):
        self.storage = storage

        # Restore all our data into the underlying dictionary.
        self.update(storage.get(STORAGE_KEY, {}))

    def save(self):
        # Get a copy of the underlying dictionary.
        self.storage.put(STORAGE_KEY, dict(self))

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.save()

