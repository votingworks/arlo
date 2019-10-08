import pytest
from binpacking import Bucket, BucketList, BalancedBucketList


@pytest.fixture
def bucket():
    yield Bucket('1')

@pytest.fixture
def bucketlist():
    buckets = []

    b = Bucket('1')
    b.add_batch('1', 100)
    b.add_batch('2', 50)
    buckets.append(b)

    b = Bucket('2')
    b.add_batch('3', 100)
    b.add_batch('4', 150)
    buckets.append(b)

    b = Bucket('3')
    b.add_batch('5', 50)
    b.add_batch('6', 50)
    buckets.append(b)

    b = Bucket('4')
    b.add_batch('7', 100)
    b.add_batch('8', 200)
    buckets.append(b)

    yield BucketList(buckets)

@pytest.fixture
def balancedbucketlist():
    buckets = []

    b = Bucket('1')
    b.add_batch('1', 100)
    b.add_batch('2', 50)
    buckets.append(b)

    b = Bucket('2')
    b.add_batch('3', 100)
    b.add_batch('4', 150)
    buckets.append(b)

    b = Bucket('3')
    b.add_batch('5', 50)
    b.add_batch('6', 50)
    buckets.append(b)

    b = Bucket('4')
    b.add_batch('7', 100)
    b.add_batch('8', 200)
    buckets.append(b)

    yield BalancedBucketList(buckets)

class TestBucket:
    def test_init(self, bucket):
        assert bucket.name == '1', 'name failed, expected {}, got {}'.format('1', bucket.name)
        assert not bucket.size , 'Initial bucket size was {}, not 0'.format(bucket.size)
        assert not bucket.batches, 'Initial batches were non-empty: {}'.format(bucket.batches)
        assert not bucket.largest_element, 'Initial largest element was not None'.format(bucket.largest_element)

    def test_add_batch(self, bucket):
        expected_batches = {'1': 100}
        bucket.add_batch('1', 100)
        expected_size = 100
        assert bucket.batches == expected_batches, 'add_batch batches failed, got {}, expected {}'.format(bucket.batches, expected_batches)
        assert bucket.size == expected_size, 'add_batch size failed, got {}, expected {}'.format(bucket.size, expected_size)
        assert bucket.largest_element == '1', 'add_batch largest_element  failed, got {}, expected {}'.format(bucket.largest_element, '1')

        expected_batches = {'1': 100, '2': 50}
        bucket.add_batch('2', 50)
        expected_size += 50
        assert bucket.batches == expected_batches, 'add_batch batches failed, got {}, expected {}'.format(bucket.batches, expected_batches)
        assert bucket.size == expected_size, 'add_batch size failed, got {}, expected {}'.format(bucket.size, expected_size)
        assert bucket.largest_element == '1', 'add_batch largest_element  failed, got {}, expected {}'.format(bucket.largest_element, '1')

        expected_batches = {'1': 100, '2': 50, '3': 150}
        bucket.add_batch('3', 150)
        expected_size += 150
        assert bucket.batches == expected_batches, 'add_batch batches failed, got {}, expected {}'.format(bucket.batches, expected_batches)
        assert bucket.size == expected_size, 'add_batch size failed, got {}, expected {}'.format(bucket.size, expected_size)
        assert bucket.largest_element == '3', 'add_batch largest_element  failed, got {}, expected {}'.format(bucket.largest_element, '3')


    def test_remove_batch(self, bucket):
        bucket.add_batch('1', 100)
        bucket.add_batch('2', 50)
        bucket.add_batch('3', 150)

        rem = bucket.remove_batch('1')

        expected_batches = {'2': 50, '3': 150}
        expected_size = 200
        expected_rem = {'1': 100}
        expected_largest = '3'

        assert rem == expected_rem, 'remove_batch returned {}, expected {}'.format(rem, expected_rem)
        assert bucket.largest_element == expected_largest, 'remove_batch changed largest to {}, should still be {}'.format(bucket.largest_element, expected_largest)
        assert bucket.batches == expected_batches, 'remove_batch resulted in batches {}, should be {}'.format(bucket.batches, expected_batches)
        assert bucket.size == expected_size, 'remove_batch resulted in size {}, expected size{}'.format(bucket.size, expected_size)
        
        rem = bucket.remove_batch('3')

        expected_batches = {'2': 50}
        expected_size = 50
        expected_rem = {'3': 150}
        expected_largest = '2'

        assert rem == expected_rem, 'remove_batch returned {}, expected {}'.format(rem, expected_rem)
        assert bucket.largest_element == expected_largest, 'remove_batch changed largest to {}, should still be {}'.format(bucket.largest_element, expected_largest)
        assert bucket.batches == expected_batches, 'remove_batch resulted in batches {}, should be {}'.format(bucket.batches, expected_batches)
        assert bucket.size == expected_size, 'remove_batch resulted in size {}, expected size{}'.format(bucket.size, expected_size)

    def test_repr(self, bucket):
        expected = {'name': '1', 'size': 0, 'batches': {}, 'largest element': None}
        assert str(bucket) == str(expected), 'repr failed, expected {}, got {}'.format(str(expected), str(bucket))

        bucket.add_batch('1', 100)
        expected = {'name': '1', 'size': 100, 'batches': {'1': 100}, 'largest element': '1'}
        assert str(bucket) == str(expected), 'repr failed, expected {}, got {}'.format(str(expected), str(bucket))


class TestBucketList:

    def test_init(self, bucketlist):
        assert bucketlist.avg_size == 200, 'Expected avg_size of {}, got {}'.format(200, bucketlist.avg_size)

    def test_balance(self, bucketlist):
        new_bl = bucketlist.balance()

        assert bucketlist.deviation() >= new_bl.deviation(), 'Balanced list has higher deviation than original assignment! {} is greater than {}'.format(new_bl.deviation(), bucketlist.deviation())

        num_batches = sum([len(b.batches) for b in bucketlist.buckets])
        balanced_num_batches = sum([len(b.batches) for b in new_bl.buckets])
        
        assert num_batches == balanced_num_batches, 'New batch has different number of batches than expected! Got {}, expected {}'.format(balanced_num_batches, num_batches)

        batches = set()
        [batches.union(s) for s in[set(batch.keys()) for batch in [b.batches for b in bucketlist.buckets]]]
        new_batches = set()
        [new_batches.union(s) for s in [set(batch.keys()) for batch in [b.batches for b in new_bl.buckets]]]

        assert batches == new_batches, 'Balanced batches were not the same as original batches!'

class TestBalancedBucketList:
    def test_init(self, balancedbucketlist):
        assert balancedbucketlist.avg_size == 200, 'Expected avg_size of {}, got {}'.format(200, bucketlist.avg_size)

    def test_is_balanced(self, bucketlist, balancedbucketlist):
        new_bl = bucketlist.balance()
        bbl = balancedbucketlist #for convenience

        assert new_bl.avg_size == bbl.avg_size, 'BalancedBucketList average size not the same! got {}, expected {}'.format(bbl.avg_size, new_bl.avg_size)

        assert new_bl.deviation() == bbl.deviation(), 'BalancedBucketList has a different deviation! got {}, expected {}'.format(bbl.deviation, new_bl.deviation)

        num_batches = sum([len(b.batches) for b in bucketlist.buckets])
        balanced_num_batches = sum([len(b.batches) for b in bbl.buckets])
        
        assert num_batches == balanced_num_batches, 'BalancedBucketList has different number of batches than expected! Got {}, expected {}'.format(balanced_num_batches, num_batches)

        batches = set()
        [batches.union(s) for s in[set(batch.keys()) for batch in [b.batches for b in bucketlist.buckets]]]
        new_batches = set()
        [new_batches.union(s) for s in [set(batch.keys()) for batch in [b.batches for b in bbl.buckets]]]

        assert batches == new_batches, 'Balanced batches were not the same as original batches!'

