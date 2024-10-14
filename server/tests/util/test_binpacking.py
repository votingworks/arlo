# pylint: disable=consider-using-f-string
import pytest
from ...util.binpacking import Bucket, BucketList, BalancedBucketList


@pytest.fixture
def bucket():
    return Bucket("1")


@pytest.fixture
def bucketlist():
    buckets = []

    bucket = Bucket("1")
    bucket.add_batch("1", 100)
    bucket.add_batch("2", 50)
    buckets.append(bucket)

    bucket = Bucket("2")
    bucket.add_batch("3", 100)
    bucket.add_batch("4", 150)
    buckets.append(bucket)

    bucket = Bucket("3")
    bucket.add_batch("5", 50)
    bucket.add_batch("6", 50)
    buckets.append(bucket)

    bucket = Bucket("4")
    bucket.add_batch("7", 100)
    bucket.add_batch("8", 200)
    buckets.append(bucket)

    return BucketList(buckets)


@pytest.fixture
def skewedbucketlist():
    buckets = []

    bucket = Bucket("1")
    bucket.add_batch("1", 100)
    bucket.add_batch("2", 50)
    buckets.append(bucket)

    bucket = Bucket("2")
    bucket.add_batch("3", 100)
    bucket.add_batch("4", 150)
    buckets.append(bucket)

    bucket = Bucket("3")
    bucket.add_batch("5", 50)
    bucket.add_batch("6", 50)
    buckets.append(bucket)

    bucket = Bucket("4")
    bucket.add_batch("7", 100)
    bucket.add_batch("8", 4000)
    buckets.append(bucket)

    return BucketList(buckets)


@pytest.fixture
def balancedbucketlist():
    buckets = []

    bucket = Bucket("1")
    bucket.add_batch("1", 100)
    bucket.add_batch("2", 50)
    buckets.append(bucket)

    bucket = Bucket("2")
    bucket.add_batch("3", 100)
    bucket.add_batch("4", 150)
    buckets.append(bucket)

    bucket = Bucket("3")
    bucket.add_batch("5", 50)
    bucket.add_batch("6", 50)
    buckets.append(bucket)

    bucket = Bucket("4")
    bucket.add_batch("7", 100)
    bucket.add_batch("8", 200)
    buckets.append(bucket)

    return BalancedBucketList(buckets)


@pytest.fixture
def balancedskewedbucketlist(skewedbucketlist):
    return skewedbucketlist.balance()


class TestBucket:
    def test_init(self, bucket):
        assert bucket.name == "1", "name failed, expected {}, got {}".format(
            "1", bucket.name
        )
        assert not bucket.size, "Initial bucket size was {}, not 0".format(bucket.size)
        assert not bucket.batches, "Initial batches were non-empty: {}".format(
            bucket.batches
        )
        assert (
            not bucket.largest_element
        ), "Initial largest element was not None: {}".format(bucket.largest_element)

    def test_add_batch(self, bucket):
        expected_batches = {"1": 100}
        bucket.add_batch("1", 100)
        expected_size = 100
        assert (
            bucket.batches == expected_batches
        ), "add_batch batches failed, got {}, expected {}".format(
            bucket.batches, expected_batches
        )
        assert (
            bucket.size == expected_size
        ), "add_batch size failed, got {}, expected {}".format(
            bucket.size, expected_size
        )
        assert (
            bucket.largest_element == "1"
        ), "add_batch largest_element  failed, got {}, expected {}".format(
            bucket.largest_element, "1"
        )

        expected_batches = {"1": 100, "2": 50}
        bucket.add_batch("2", 50)
        expected_size += 50
        assert (
            bucket.batches == expected_batches
        ), "add_batch batches failed, got {}, expected {}".format(
            bucket.batches, expected_batches
        )
        assert (
            bucket.size == expected_size
        ), "add_batch size failed, got {}, expected {}".format(
            bucket.size, expected_size
        )
        assert (
            bucket.largest_element == "1"
        ), "add_batch largest_element  failed, got {}, expected {}".format(
            bucket.largest_element, "1"
        )

        expected_batches = {"1": 100, "2": 50, "3": 150}
        bucket.add_batch("3", 150)
        expected_size += 150
        assert (
            bucket.batches == expected_batches
        ), "add_batch batches failed, got {}, expected {}".format(
            bucket.batches, expected_batches
        )
        assert (
            bucket.size == expected_size
        ), "add_batch size failed, got {}, expected {}".format(
            bucket.size, expected_size
        )
        assert (
            bucket.largest_element == "3"
        ), "add_batch largest_element  failed, got {}, expected {}".format(
            bucket.largest_element, "3"
        )

    def test_remove_batch(self, bucket):
        bucket.add_batch("1", 100)
        bucket.add_batch("2", 50)
        bucket.add_batch("3", 150)

        rem = bucket.remove_batch("1")

        expected_batches = {"2": 50, "3": 150}
        expected_size = 200
        expected_rem = {"1": 100}
        expected_largest = "3"

        assert rem == expected_rem, "remove_batch returned {}, expected {}".format(
            rem, expected_rem
        )
        assert (
            bucket.largest_element == expected_largest
        ), "remove_batch changed largest to {}, should still be {}".format(
            bucket.largest_element, expected_largest
        )
        assert (
            bucket.batches == expected_batches
        ), "remove_batch resulted in batches {}, should be {}".format(
            bucket.batches, expected_batches
        )
        assert (
            bucket.size == expected_size
        ), "remove_batch resulted in size {}, expected size{}".format(
            bucket.size, expected_size
        )

        rem = bucket.remove_batch("3")

        expected_batches = {"2": 50}
        expected_size = 50
        expected_rem = {"3": 150}
        expected_largest = "2"

        assert rem == expected_rem, "remove_batch returned {}, expected {}".format(
            rem, expected_rem
        )
        assert (
            bucket.largest_element == expected_largest
        ), "remove_batch changed largest to {}, should still be {}".format(
            bucket.largest_element, expected_largest
        )
        assert (
            bucket.batches == expected_batches
        ), "remove_batch resulted in batches {}, should be {}".format(
            bucket.batches, expected_batches
        )
        assert (
            bucket.size == expected_size
        ), "remove_batch resulted in size {}, expected size{}".format(
            bucket.size, expected_size
        )

        rem = bucket.remove_batch("2")

        expected_batches = {}
        expected_size = 0
        expected_rem = {"2": 50}
        expected_largest = None
        assert rem == expected_rem, "remove_batch returned {}, expected {}".format(
            rem, expected_rem
        )
        assert (
            bucket.largest_element == expected_largest
        ), "remove_batch changed largest to {}, should still be {}".format(
            bucket.largest_element, expected_largest
        )
        assert (
            bucket.batches == expected_batches
        ), "remove_batch resulted in batches {}, should be {}".format(
            bucket.batches, expected_batches
        )
        assert (
            bucket.size == expected_size
        ), "remove_batch resulted in size {}, expected size{}".format(
            bucket.size, expected_size
        )

    def test_comparator(self, bucket):
        bucket.add_batch("1", 100)
        bucket.add_batch("2", 50)
        bucket.add_batch("3", 150)

        other_bucket = Bucket("1")
        other_bucket.add_batch("1", 100)
        other_bucket.add_batch("2", 50)
        other_bucket.add_batch("3", 150)

        assert not bucket > other_bucket
        assert bucket == other_bucket

        other_bucket.name = "2"
        assert bucket != other_bucket

        not_bucket = 3
        assert not_bucket != bucket
        assert not_bucket != other_bucket

        other_bucket.remove_batch("2")

        assert bucket > other_bucket

        bucket.remove_batch("3")

        assert other_bucket > bucket

    def test_repr(self, bucket):
        expected = {"name": "1", "size": 0, "batches": {}, "largest element": None}
        assert str(bucket) == str(expected), "repr failed, expected {}, got {}".format(
            str(expected), str(bucket)
        )

        bucket.add_batch("1", 100)
        expected = {
            "name": "1",
            "size": 100,
            "batches": {"1": 100},
            "largest element": "1",
        }
        assert str(bucket) == str(expected), "repr failed, expected {}, got {}".format(
            str(expected), str(bucket)
        )


class TestBucketList:
    def test_init(self, bucketlist):
        assert bucketlist.avg_size == 200, "Expected avg_size of {}, got {}".format(
            200, bucketlist.avg_size
        )

    def test_balance(self, bucketlist):
        new_bl = bucketlist.balance()

        assert (
            bucketlist.deviation() >= new_bl.deviation()
        ), "Balanced list has higher deviation than original assignment! {} is greater than {}".format(
            new_bl.deviation(), bucketlist.deviation()
        )

        num_batches = sum(len(bucket.batches) for bucket in bucketlist.buckets)
        balanced_num_batches = sum(len(bucket.batches) for bucket in new_bl.buckets)

        assert (
            num_batches == balanced_num_batches
        ), "New batch has different number of batches than expected! Got {}, expected {}".format(
            balanced_num_batches, num_batches
        )

        batches = {batch for bucket in bucketlist.buckets for batch in bucket.batches}
        new_batches = {batch for bucket in new_bl.buckets for batch in bucket.batches}

        assert (
            batches == new_batches
        ), "Balanced batches were not the same as original batches!"

    def test_balance_skewed(self, skewedbucketlist):
        new_bl = skewedbucketlist.balance()

        assert (
            skewedbucketlist.deviation() >= new_bl.deviation()
        ), "Balanced list has higher deviation than original assignment! {} is greater than {}".format(
            new_bl.deviation(), skewedbucketlist.deviation()
        )

        num_batches = sum(len(bucket.batches) for bucket in skewedbucketlist.buckets)
        balanced_num_batches = sum(len(bucket.batches) for bucket in new_bl.buckets)

        assert (
            num_batches == balanced_num_batches
        ), "New batch has different number of batches than expected! Got {}, expected {}".format(
            balanced_num_batches, num_batches
        )

        batches = {
            batch for bucket in skewedbucketlist.buckets for batch in bucket.batches
        }
        new_batches = {batch for bucket in new_bl.buckets for batch in bucket.batches}

        assert (
            batches == new_batches
        ), "Balanced batches were not the same as original batches!"

    def test_repr_print(self, bucketlist):
        expected = [
            {
                "name": "1",
                "size": 150,
                "batches": {"1": 100, "2": 50},
                "largest element": "1",
            },
            {
                "name": "2",
                "size": 250,
                "batches": {"3": 100, "4": 150},
                "largest element": "4",
            },
            {
                "name": "3",
                "size": 100,
                "batches": {"5": 50, "6": 50},
                "largest element": "5",
            },
            {
                "name": "4",
                "size": 300,
                "batches": {"7": 100, "8": 200},
                "largest element": "8",
            },
        ]

        assert str(bucketlist) == str(
            expected
        ), "repr failed, expected {}, got {}".format(str(expected), str(bucketlist))


class TestBalancedBucketList:
    def test_init(self, balancedbucketlist):
        assert (
            balancedbucketlist.avg_size == 200
        ), "Expected avg_size of {}, got {}".format(200, bucketlist.avg_size)

    def test_is_balanced(self, bucketlist, balancedbucketlist):
        new_bl = bucketlist.balance()
        bbl = balancedbucketlist  # for convenience

        assert (
            new_bl.avg_size == bbl.avg_size
        ), "BalancedBucketList average size not the same! got {}, expected {}".format(
            bbl.avg_size, new_bl.avg_size
        )

        assert (
            new_bl.deviation() == bbl.deviation()
        ), "BalancedBucketList has a different deviation! got {}, expected {}".format(
            bbl.deviation, new_bl.deviation
        )

        num_batches = sum(len(bucket.batches) for bucket in bucketlist.buckets)
        balanced_num_batches = sum(len(bucket.batches) for bucket in bbl.buckets)

        assert (
            num_batches == balanced_num_batches
        ), "BalancedBucketList has different number of batches than expected! Got {}, expected {}".format(
            balanced_num_batches, num_batches
        )

        batches = {batch for bucket in bbl.buckets for batch in bucket.batches}
        new_batches = {batch for bucket in new_bl.buckets for batch in bucket.batches}

        assert (
            batches == new_batches
        ), "Balanced batches were not the same as original batches!"

    def test_balance_skewedbalanced(self, skewedbucketlist, balancedskewedbucketlist):
        new_bl = skewedbucketlist.balance()
        bbl = balancedskewedbucketlist  # for convenience

        assert (
            new_bl.avg_size == bbl.avg_size
        ), "BalancedskewedBucketList average size not the same! got {}, expected {}".format(
            bbl.avg_size, new_bl.avg_size
        )

        assert (
            new_bl.deviation() == bbl.deviation()
        ), "BalancedskewedBucketList has a different deviation! got {}, expected {}".format(
            bbl.deviation, new_bl.deviation
        )

        num_batches = sum(len(bucket.batches) for bucket in skewedbucketlist.buckets)
        balanced_num_batches = sum(len(bucket.batches) for bucket in bbl.buckets)

        assert (
            num_batches == balanced_num_batches
        ), "BalancedskewedBucketList has different number of batches than expected! Got {}, expected {}".format(
            balanced_num_batches, num_batches
        )

        batches = {batch for bucket in bbl.buckets for batch in bucket.batches}
        new_batches = {batch for bucket in new_bl.buckets for batch in bucket.batches}

        assert (
            batches == new_batches
        ), "Balanced batches were not the same as original batches!"

    def test_get_avg_size(self, balancedbucketlist):
        assert balancedbucketlist.get_avg_size() == 200

    def test_repr(self, balancedbucketlist):
        expected = [
            {
                "name": "1",
                "size": 200,
                "batches": {"8": 200},
                "largest element": "8",
            },
            {
                "name": "2",
                "size": 200,
                "batches": {"4": 150, "5": 50},
                "largest element": "4",
            },
            {
                "name": "3",
                "size": 200,
                "batches": {"1": 100, "7": 100},
                "largest element": "1",
            },
            {
                "name": "4",
                "size": 200,
                "batches": {"3": 100, "2": 50, "6": 50},
                "largest element": "3",
            },
        ]

        assert str(balancedbucketlist) == str(
            expected
        ), "repr failed, expected {}, got {}".format(
            str(expected), str(balancedbucketlist)
        )
