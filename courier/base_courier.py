from abc import ABC, abstractmethod

class BaseCourier(ABC):
    @abstractmethod
    def track(self, numbers,order_map):
        """
        Input: List of tracking numbers (strings)
        Output: List of dicts: [{'number': str, 'status': str, 'time': str}]
        """
        self.order_map = order_map
        pass