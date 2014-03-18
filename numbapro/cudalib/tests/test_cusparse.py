import numpy as np
import scipy.sparse
import unittest
from .support import addtest, main
from numbapro.cudalib import cusparse
from numbapro.cudalib.cusparse.binding import CuSparseError
from numbapro import cuda


@addtest
class TestCuSparseLevel1(unittest.TestCase):
    def setUp(self):
        self.cus = cusparse.Sparse()

    def generic_test_axpyi(self, dtype):
        alpha = 2
        xval = np.arange(5, dtype=dtype) + 1
        xind = np.arange(xval.size, dtype='int32') * 2
        y = np.zeros(shape=xval.size * 2, dtype=xval.dtype)
        self.cus.axpyi(alpha, xval, xind, y)
        self.assertTrue(np.allclose(y[xind], (xval * 2)))

    def test_Saxpyi(self):
        self.generic_test_axpyi(dtype=np.float32)

    def test_Daxpyi(self):
        self.generic_test_axpyi(dtype=np.float64)

    def test_Caxpyi(self):
        self.generic_test_axpyi(dtype=np.complex64)

    def test_Zaxpyi(self):
        self.generic_test_axpyi(dtype=np.complex128)

    def generic_test_doti(self, dtype):
        xval = np.arange(5, dtype=dtype) + 1
        xind = np.arange(xval.size, dtype='int32') * 2
        y = np.ones(shape=xval.size * 2, dtype=xval.dtype)
        result = self.cus.doti(xval, xind, y)
        self.assertTrue(result)

    def test_Sdoti(self):
        self.generic_test_doti(dtype=np.float32)

    def test_Zdoti(self):
        self.generic_test_doti(dtype=np.complex128)

    def generic_test_dotci(self, dtype):
        xval = np.arange(5, dtype=dtype) + 1
        xind = np.arange(xval.size, dtype='int32') * 2
        y = np.ones(shape=xval.size * 2, dtype=xval.dtype)
        result = self.cus.dotci(xval, xind, y)
        self.assertTrue(result)

    def test_Zdotci(self):
        self.generic_test_dotci(dtype=np.complex128)

    def generic_test_gthr(self, dtype):
        xval = np.arange(5, dtype=dtype) + 1
        xind = np.arange(xval.size, dtype='int32') * 2
        y = np.ones(shape=xval.size * 2, dtype=xval.dtype)
        self.cus.gthr(y, xval, xind)
        self.assertTrue(np.all(xval == 1))

    def test_Sgthr(self):
        self.generic_test_gthr(dtype=np.float32)

    def test_Cgthr(self):
        self.generic_test_gthr(dtype=np.complex64)

    def generic_test_gthrz(self, dtype):
        xval = np.arange(5, dtype=dtype) + 1
        xind = np.arange(xval.size, dtype='int32') * 2
        y = np.ones(shape=xval.size * 2, dtype=xval.dtype)
        self.cus.gthrz(y, xval, xind)
        self.assertTrue(np.all(xval == 1))
        self.assertTrue(np.all(y[xind] == 0))

    def test_Dgthr(self):
        self.generic_test_gthrz(dtype=np.float64)

    def test_Zgthr(self):
        self.generic_test_gthrz(dtype=np.complex128)

    def generic_test_roti(self, dtype):
        xval = np.arange(5, dtype=dtype) + 1
        xind = np.arange(xval.size, dtype='int32') * 2
        y = np.ones(shape=xval.size * 2, dtype=xval.dtype)
        c = .2
        s = .3
        oldxval = xval.copy()
        oldy = y.copy()
        self.cus.roti(xval, xind, y, c, s)
        self.assertFalse(np.all(oldxval == xval))
        self.assertFalse(np.all(oldy == y))

    def test_Sroti(self):
        self.generic_test_roti(dtype=np.float32)

    def test_Droti(self):
        self.generic_test_roti(dtype=np.float64)

    def generic_test_sctr(self, dtype):
        xval = np.arange(5, dtype=dtype) + 1
        xind = np.arange(xval.size, dtype='int32') * 2
        y = np.ones(shape=xval.size * 2, dtype=xval.dtype)
        oldy = y.copy()
        self.cus.sctr(xval, xind, y)
        self.assertFalse(np.all(oldy == y))

    def test_Ssctr(self):
        self.generic_test_sctr(dtype=np.float32)

    def test_Csctr(self):
        self.generic_test_sctr(dtype=np.complex64)


@addtest
class TestCuSparseMatrixOp(unittest.TestCase):
    def test_bsr_matrix(self):
        row = np.array([0, 0, 1, 2, 2, 2])
        col = np.array([0, 2, 2, 0, 1, 2])
        data = np.array([1, 2, 3, 4, 5, 6])
        expect = scipy.sparse.bsr_matrix((data, (row, col)), shape=(3, 3))
        mat = cusparse.bsr_matrix((data, (row, col)), shape=(3, 3))
        host = mat.copy_to_host()
        self.assertTrue(np.all(host.indices == expect.indices))
        self.assertTrue(np.all(host.indptr == expect.indptr))
        self.assertTrue(np.all(host.data == expect.data))

    def test_matdescr(self):
        sparse = cusparse.Sparse()
        md = sparse.matdescr()
        md.diagtype = 'N'
        md.fillmode = 'L'
        md.indexbase = 0
        md.matrixtype = 'G'

        self.assertEqual('N', md.diagtype)
        self.assertEqual('L', md.fillmode)
        self.assertEqual(0, md.indexbase)
        self.assertEqual('G', md.matrixtype)
        del md


@addtest
class TestCuSparseLevel2(unittest.TestCase):
    def setUp(self):
        self.cus = cusparse.Sparse()

    def generic_test_bsrmv(self, dtype):
        row = np.array([0, 0, 1, 2, 2, 2])
        col = np.array([0, 2, 2, 0, 1, 2])
        data = np.array([1, 2, 3, 4, 5, 6], dtype=dtype)

        bsrmat = cusparse.bsr_matrix((data, (row, col)), shape=(3, 3))
        x = np.ones(3, dtype=dtype)
        y = np.ones(3, dtype=dtype)
        oldy = y.copy()

        alpha = 1
        beta = 1
        descr = self.cus.matdescr()
        self.cus.bsrmv_matrix('C', 'N', alpha, descr, bsrmat, x, beta, y)

        self.assertFalse(np.all(y == oldy))

    def test_Sbsrmv(self):
        dtype = np.float32
        self.generic_test_bsrmv(dtype=dtype)

    def test_Cbsrmv(self):
        dtype = np.complex64
        self.generic_test_bsrmv(dtype=dtype)

    def test_Sbsrxmv(self):
        """
        Just exercise the codepath
        """
        dtype = np.float32
        alpha = 0
        beta = 0
        descr = self.cus.matdescr()
        bsrVal = np.zeros(10, dtype=dtype)
        bsrMaskPtr = np.zeros(10, dtype=np.int32)
        bsrRowPtr = np.zeros(10, dtype=np.int32)
        bsrEndPtr = np.zeros(10, dtype=np.int32)
        bsrColInd = np.zeros(10, dtype=np.int32)
        blockDim = 1
        x = np.zeros(10, dtype=dtype)
        y = np.zeros(10, dtype=dtype)
        self.cus.bsrxmv('C', 'N', 1, 1, 1, 1, alpha, descr, bsrVal,
                        bsrMaskPtr, bsrRowPtr, bsrEndPtr, bsrColInd,
                        blockDim, x, beta, y)

    def test_Scsrmv(self):
        """
        Just exercise the codepath
        """
        dtype = np.float32
        alpha = 0
        beta = 0
        descr = self.cus.matdescr()
        csrVal = np.zeros(10, dtype=dtype)
        csrColInd = np.zeros(10, dtype=np.int32)
        csrRowPtr = np.zeros(10, dtype=np.int32)
        x = np.zeros(10, dtype=dtype)
        y = np.zeros(10, dtype=dtype)
        trans = 'N'
        m = 1
        n = 1
        nnz = 1
        self.cus.csrmv(trans, m, n, nnz, alpha, descr, csrVal, csrRowPtr,
                       csrColInd, x, beta, y)

    def test_Scsrmv(self):
        """
        Just exercise the codepath
        """
        dtype = np.float32

        descr = self.cus.matdescr()
        csrVal = np.zeros(10, dtype=dtype)
        csrColInd = np.zeros(10, dtype=np.int32)
        csrRowPtr = np.zeros(10, dtype=np.int32)
        trans = 'N'
        m = 1
        nnz = 1
        info = self.cus.csrsv_analysis(trans, m, nnz, descr, csrVal,
                                       csrRowPtr, csrColInd)

        alpha = 1.0
        x = np.zeros(10, dtype=dtype)
        y = np.zeros(10, dtype=dtype)
        try:
            self.cus.csrsv_solve(trans, m, alpha, descr, csrVal, csrRowPtr,
                                 csrColInd, info, x, y)
        except CuSparseError:
            pass


@addtest
class TestCuSparseLevel3(unittest.TestCase):
    def setUp(self):
        self.cus = cusparse.Sparse()

    def test_Scsrmm(self):
        """
        Just exercise the codepath
        """
        dtype = np.float32

        descrA = self.cus.matdescr()
        B = C = csrValA = np.zeros(10, dtype=dtype)
        csrColIndA = np.zeros(10, dtype=np.int32)
        csrRowPtrA = np.zeros(10, dtype=np.int32)
        ldb = 1
        ldc = 1
        m = 1
        n = 1
        k = 1
        nnz = 1
        alpha = 1
        beta = 1
        transA = 'N'
        self.cus.csrmm(transA, m, n, k, nnz, alpha, descrA, csrValA,
                       csrRowPtrA, csrColIndA, B, ldb, beta, C, ldc)

    def test_Ccsrmm(self):
        """
        Just exercise the codepath
        """
        dtype = np.complex64

        descrA = self.cus.matdescr()
        B = C = csrValA = np.zeros(10, dtype=dtype)
        csrColIndA = np.zeros(10, dtype=np.int32)
        csrRowPtrA = np.zeros(10, dtype=np.int32)
        ldb = 1
        ldc = 1
        m = 1
        n = 1
        k = 1
        nnz = 1
        alpha = 1
        beta = 1
        transA = transB = 'N'
        try:
            self.cus.csrmm2(transA, transB, m, n, k, nnz, alpha, descrA,
                            csrValA,
                            csrRowPtrA, csrColIndA, B, ldb, beta, C, ldc)
        except CuSparseError:
            pass

    def test_Scsrsm(self):
        """
        Just exercise the codepath
        """
        dtype = np.float32

        descrA = self.cus.matdescr()
        X = Y = csrValA = np.zeros(10, dtype=dtype)
        csrColIndA = np.zeros(10, dtype=np.int32)
        csrRowPtrA = np.zeros(10, dtype=np.int32)
        m = 1
        n = 1
        nnz = 1
        transA = 'N'
        # try:
        info = self.cus.csrsm_analysis(transA, m, nnz, descrA, csrValA,
                                       csrRowPtrA, csrColIndA)
        # except CuSparseError:
        #     pass
        alpha = 1
        ldx = 1
        ldy = 1
        self.cus.csrsm_solve(transA, m, n, alpha, descrA, csrValA,
                             csrRowPtrA, csrColIndA, info, X, ldx, Y, ldy)


@addtest
class TestCuSparseExtra(unittest.TestCase):
    def setUp(self):
        self.cus = cusparse.Sparse()

    def test_XcsrgeamNnz(self):
        """
        Just exercise the codepath
        """
        m = n = 1
        nnzA = 1
        nnzB = 1
        descrA = descrB = descrC = self.cus.matdescr()
        csrColIndA = csrColIndB = np.zeros(10, dtype=np.int32)
        csrRowPtrA = csrRowPtrB = csrRowPtrC = np.zeros(10, dtype=np.int32)
        nnzC = self.cus.XcsrgeamNnz(m, n, descrA, nnzA, csrRowPtrA, csrColIndA,
                                    descrB, nnzB, csrRowPtrB, csrColIndB,
                                    descrC,
                                    csrRowPtrC)
        self.assertTrue(isinstance(nnzC, int))

    def test_Scsrgeam(self):
        """
        Just exercise the codepath
        """
        dtype = np.float32
        m = n = 1
        nnzA = 1
        nnzB = 1
        alpha = beta = 1
        csrValA = csrValB = csrValC = np.zeros(10, dtype=dtype)
        descrA = descrB = descrC = self.cus.matdescr()
        csrColIndA = csrColIndB = csrColIndC = np.zeros(10, dtype=np.int32)
        csrRowPtrA = csrRowPtrB = csrRowPtrC = np.zeros(10, dtype=np.int32)
        self.cus.csrgeam(m, n, alpha, descrA, nnzA, csrValA, csrRowPtrA,
                         csrColIndA, beta, descrB, nnzB, csrValB,
                         csrRowPtrB, csrColIndB, descrC, csrValC,
                         csrRowPtrC, csrColIndC)


    def XcsrgemmNnz(self):
        """
        Just exercise the codepath
        """
        m = n = k = 1
        nnzA = 1
        nnzB = 1
        descrA = descrB = descrC = self.cus.matdescr()
        csrColIndA = csrColIndB = np.zeros(10, dtype=np.int32)
        csrRowPtrA = csrRowPtrB = csrRowPtrC = np.zeros(10, dtype=np.int32)
        transA = transB = 'N'
        nnzC = self.cus.XcsrgemmNnz(transA, transB, m, n, k, descrA, nnzA,
                                    csrRowPtrA,
                                    csrColIndA, descrB, nnzB, csrRowPtrB,
                                    csrColIndB, descrC,
                                    csrRowPtrC)
        self.assertTrue(isinstance(nnzC, int))

    def test_Scsrgemm(self):
        """
        Just exercise the codepath
        """
        dtype = np.float32
        m = n = k = 0
        transA = transB = 'N'
        nnzA = 0
        nnzB = 0
        csrValA = csrValB = csrValC = np.zeros(10, dtype=dtype)
        descrA = descrB = descrC = self.cus.matdescr()
        csrColIndA = csrColIndB = csrColIndC = np.zeros(10, dtype=np.int32)
        csrRowPtrA = csrRowPtrB = csrRowPtrC = np.zeros(10, dtype=np.int32)
        self.cus.csrgemm(transA, transB, m, n, k, descrA, nnzA, csrValA,
                         csrRowPtrA, csrColIndA, descrB, nnzB, csrValB,
                         csrRowPtrB,
                         csrColIndB, descrC, csrValC, csrRowPtrC, csrColIndC)


if __name__ == '__main__':
    main()

