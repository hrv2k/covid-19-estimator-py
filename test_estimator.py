import unittest
from src.estimator import currently_infected, infections_by_requested_time

class Test(unittest.TestCase):

    def test_currently_infected(self):
        self.assertEqual(currently_infected(10,10),100)
        self.assertEqual(currently_infected(10,50),500)
    

    def test_infections_by_requested_time(self):
        self.assertEqual(infections_by_requested_time(10,28), 5120)


if __name__ == '__main__':
    unittest.main()