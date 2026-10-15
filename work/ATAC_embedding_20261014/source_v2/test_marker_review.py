import unittest
import numpy as np
from scipy import sparse
from marker_review import aggregate
class MarkerTests(unittest.TestCase):
 def test_animal_membership_and_raw_preservation(self):
  x=sparse.csr_matrix([[2,0],[0,3],[1,4]],dtype=np.int32);original=x.copy();r,d,l=aggregate(x,np.array([2.,3.,5.]),np.array([1,0,1]),2)
  np.testing.assert_array_equal(r,[[0,3],[3,4]]);np.testing.assert_array_equal(d,[[0,1],[2,1]]);self.assertEqual((x!=original).nnz,0);self.assertTrue(np.isfinite(l).all())
 def test_fractional_or_misaligned_inputs_refused(self):
  with self.assertRaises(ValueError):aggregate(sparse.csr_matrix([[.5]]),np.array([1.]),np.array([0]),1)
  with self.assertRaises(ValueError):aggregate(sparse.csr_matrix([[1]],dtype=np.int32),np.array([1.]),np.array([2]),1)
if __name__=='__main__':unittest.main()
