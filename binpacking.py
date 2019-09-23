import csv
import operator

class Bucket:

    def __init__(self, name):
        self.name = name
        self.size = 0
        self.batches = {}
        self.largest_element = None


    def add_batch(self, batch_name, batch_size):
        self.batches[batch_name] = batch_size
        self.size += batch_size

        if not self.largest_element:
            self.largest_element = batch_name
        elif batch_size > self.batches[self.largest_element]:
            self.largest_element = batch_name

    def remove_batch(self, batch_name):
        taken = self.batches.pop(batch_name)
        self.size -= taken

        if not self.size:
            self.largest_element = None
        elif batch_name == self.largest_element:
            self.largest_element = next(iter(self.batches))
            for b in self.batches:
                if self.batches[b] > self.batches[self.largest_element]:
                    self.largest_element = b



        return({batch_name: taken})

    def __repr__(self):
        ret_str = {
            'name': self.name,
            'size': self.size,
            'batches': self.batches,
            'largest element': self.largest_element
        }
        return str(ret_str)
    
    def __eq__(self, other):
        return self.name == other.name

class BucketList:

    def __init__(self, buckets):

        self.buckets = buckets
        self.avg_size = self.get_avg_size() 
        self.biggest = self.get_biggest()
        self.smallest = self.get_smallest()

    def get_avg_size(self):
        return sum([s.size for s in self.buckets])/len(self.buckets)

    def get_biggest(self):
        biggest = self.buckets[0]
        for bucket in self.buckets:
            if bucket.size > biggest.size:
                biggest = bucket
        return biggest

    def get_smallest(self):
        smallest = self.biggest
        for bucket in self.buckets:
            if bucket.size < smallest.size:
                smallest = bucket

        return smallest

    def get_too_big(self):
        return [s.name for s in self.buckets if s.size >= self.avg_size]


    def get_too_small(self):
        return [s.name for s in self.buckets if s.size < self.avg_size]

    def balance(self):
        print(self.biggest.size, self.avg_size)
        # Implements https://stackoverflow.com/questions/16588669/spread-objects-evenly-over-multiple-collections

        for bucket_name in sorted(self.get_too_big()):
            bucket = self.buckets[bucket_name]

            # Remove the biggest element from the biggest bucket
            if bucket.size - bucket.batches[bucket.largest_element] > self.avg_size:
                rem = bucket.remove_batch(bucket.largest_element)
                r_name = next(iter(rem))

                self.smallest.add_batch(r_name, rem[r_name])
                self.smallest = self.get_smallest()
                self.biggest = self.get_biggest()

        for bucket in sorted(self.get_too_small()):
            for bigger_name in sorted(self.get_too_big(), reverse=True):
                bigger = self.buckets[bigger_name]

                for item in sorted(bigger.batches, reverse=True):
                    if bigger.size - bigger.batches[item] > self.avg_size:
                        rem = bigger.remove_batch(item)
                        r_name = next(iter(rem))

                        self.buckets[bucket].add_batch(r_name, rem[r_name])
                        self.smallest = self.get_smallest()
                        self.biggest = self.get_biggest()


                    
        print(self.biggest.size, self.avg_size)

    def __gt__(self, other):
        return self.size > other.size

    def __repr__(self):
        return str(self.buckets)

    def pretty_print(self):
        for bucket in self.buckets:
            print(bucket.name, bucket.size)
            for batch in bucket.batches:
                print('\t', batch, bucket.batches[batch])
