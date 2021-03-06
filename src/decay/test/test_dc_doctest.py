import doctest
import nose.tools as nt
import sys, os
sys.path.insert(0, os.pardir)
import dc_mod_doctest

def test_dc_mod_doctest():
    failure_count, test_count = doctest.testmod(m=dc_mod_doctest)
    nt.assert_equal(failure_count, 0,
                    msg='%d tests out of %d failed' %
                    (failure_count, test_count))

