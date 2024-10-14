from typing import Dict, Optional, Tuple, List, cast
import operator
import numpy


class Bucket:
    def __init__(self, name: str):
        self.name = name
        self.size = 0
        self.batches: Dict[str, int] = {}
        self.largest_element: Optional[str] = None

    def add_batch(self, batch_name: str, batch_size: int) -> None:
        self.batches[batch_name] = batch_size
        self.size += batch_size

        if not self.largest_element:
            self.largest_element = batch_name
        elif batch_size > self.batches[self.largest_element]:
            self.largest_element = batch_name

    def remove_batch(self, batch_name: str) -> Dict[str, int]:
        taken = self.batches.pop(batch_name)
        self.size -= taken

        if not self.size:
            self.largest_element = None
        elif batch_name == self.largest_element:
            self.largest_element = max(
                self.batches.items(), key=operator.itemgetter(1)
            )[0]

        return {batch_name: taken}

    def __repr__(self) -> str:
        ret_str = {
            "name": self.name,
            "size": self.size,
            "batches": self.batches,
            "largest element": self.largest_element,
        }
        return str(ret_str)

    def __gt__(self, other: "Bucket") -> bool:
        return self.size > other.size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bucket):
            return False
        return self.name == other.name


class BucketList:
    """
    A list of buckets that doesn't self-balance. For use in testing balancing
    algorithms.
    """

    def __init__(self, buckets: List[Bucket]):
        self.buckets = buckets
        self.avg_size = self.get_avg_size()

    def get_avg_size(self) -> float:
        return cast(float, numpy.mean([s.size for s in self.buckets]))

    def deviation(self) -> float:
        return sum(abs(self.avg_size - b.size) for b in self.buckets) / self.avg_size

    def balance(self) -> "BucketList":
        """
        Assign all batches that are bigger than the average size to buckets,
        minimizing the amount of size deviation from the average. Then
        iterate through all the rest of the batches and add them to the
        buckets, minimizing the deviation from the average.
        """

        # first get all the batches in a list
        batches: List[Tuple[str, int]] = []

        # TODO maybe rework the whole thing so that we don't have to create a
        # new list?
        new_buckets = []
        for bucket in self.buckets:
            new_buckets.append(Bucket(bucket.name))
            for batch_name in bucket.batches:
                batches.append((batch_name, bucket.batches[batch_name]))

        # Sort the list of batches
        batches = sorted(batches, key=operator.itemgetter(1), reverse=True)
        left_overs: List[Tuple[str, int]] = []

        # Now assign batches
        # Assign all the too-big batches first
        for i, batch in enumerate(batches):

            # Find the least-full bucket and assign this batch
            if batch[1] > self.avg_size:
                # Find the least-bad bucket
                (min_idx, _min_del) = min(
                    enumerate(
                        [
                            bucket.size + batch[1] - self.avg_size
                            for bucket in new_buckets
                        ]
                    ),
                    key=operator.itemgetter(1),
                )

                # Now add to the least-bad bucket
                new_buckets[min_idx].add_batch(batch[0], batch[1])

            else:
                left_overs = batches[i:]
                break

        # Now iterate through remaining batches and add them to the bucket
        # that will be _least_ over the average
        for batch in left_overs:
            # Find the least-bad bucket
            (min_idx, _min_del) = min(
                enumerate(
                    map(
                        # pylint: disable=cell-var-from-loop
                        lambda bucket: bucket.size + batch[1] - self.avg_size,
                        new_buckets,
                    )
                ),
                key=operator.itemgetter(1),
            )

            # Now add to the least-bad bucket
            new_buckets[min_idx].add_batch(batch[0], batch[1])

        return BucketList(new_buckets)

    def __repr__(self) -> str:
        return str(self.buckets)

    def pretty_print(self):  # pragma: no cover
        for bucket in self.buckets:
            print(bucket.name, bucket.size)
            for batch in bucket.batches:
                print("\t", batch, bucket.batches[batch])


class BalancedBucketList:
    """
    A balanced list of buckets.
    """

    avg_size: float
    buckets: List[Bucket]

    def __init__(self, buckets):
        """
        Assign all batches that are bigger than the average size to buckets,
        minimizing the amount of size deviation from the average.

        Then iterate through all the rest of the batches and add them to the
        buckets, minimizing the deviation from the average.
        """

        self.avg_size = numpy.mean([s.size for s in buckets])

        self.buckets = []

        # first get all the batches in a list, and initialize our buckets
        batches: Tuple[str, int] = []
        for bucket in buckets:
            self.buckets.append(Bucket(bucket.name))
            for batch_name in bucket.batches:
                batches.append((batch_name, bucket.batches[batch_name]))

        # Sort the list of batches
        batches = sorted(batches, key=operator.itemgetter(1), reverse=True)
        left_overs: List[Tuple[str, int]] = []

        # Now assign batches to buckets
        # Assign all the too-big batches first
        for i, batch in enumerate(batches):

            # Find the least-full bucket and assign this batch
            if batch[1] > self.avg_size:
                # Find the least-bad bucket
                (min_idx, _min_del) = min(
                    enumerate(
                        [
                            bucket.size + batch[1] - self.avg_size
                            for bucket in self.buckets
                        ]
                    ),
                    key=operator.itemgetter(1),
                )

                # Now add to the least-bad bucket
                self.buckets[min_idx].add_batch(batch[0], batch[1])

            else:
                left_overs = batches[i:]
                break

        # Now iterate through remaining batches and add them to the bucket
        # that will be _least_ over the average
        for batch in left_overs:
            # Find the least-bad bucket
            (min_idx, _min_del) = min(
                enumerate(
                    map(
                        # pylint: disable=cell-var-from-loop
                        lambda bucket: bucket.size + batch[1] - self.avg_size,
                        self.buckets,
                    )
                ),
                key=operator.itemgetter(1),
            )

            # Now add to the least-bad bucket
            self.buckets[min_idx].add_batch(batch[0], batch[1])

    def get_avg_size(self) -> float:
        return cast(float, numpy.mean([s.size for s in self.buckets]))

    def deviation(self) -> float:
        return sum(abs(self.avg_size - b.size) for b in self.buckets) / self.avg_size

    def __repr__(self) -> str:
        return str(self.buckets)

    def pretty_print(self):  # pragma: no cover
        for bucket in self.buckets:
            print(bucket.name, bucket.size)
            for batch in bucket.batches:
                print("\t", batch, bucket.batches[batch])


# batches = {}
# for line in csv.DictReader(open('washtenaw-retrieval.csv')):
#     if line['Batch Name'] in batches:
#         batches[line['Batch Name']] += 1
#     else:
#         batches[line['Batch Name']] = 1
# audit_boards = 15

# buckets = []
# for i in range(audit_boards):
#     buckets.append(Bucket(i))

# # Assigne batches to buckets
# for i, batch in enumerate(batches):
#     buckets[i%audit_boards].add_batch(str(batch), int(batches[str(batch)]))

# bl = BucketList(buckets)

# bl.pretty_print()
# bl.balance()
# bl.pretty_print()

# bl_batches = 0
# for bucket in bl.buckets:
#     bl_batches += len(bucket.batches)

# print('------')
# new_bl = BalancedBucketList(buckets)
# new_bl.pretty_print()

# nnew_bl_batches = 0
# new_bl_batches = set()
# for bucket in new_bl.buckets:
#     nnew_bl_batches += len(bucket.batches)
#     for batch in bucket.batches:
#         new_bl_batches.add(batch)


# print('////////')
# print(len(batches), bl_batches, nnew_bl_batches)
# print(bl.deviation(), new_bl.deviation())
# print(len(new_bl_batches.intersection(set(batches.keys()))))
