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

        self.bucket_map = {}
        self.buckets = []
        for i, bucket in enumerate(buckets):
            self.bucket_map[bucket.name] = i
            self.buckets.append(bucket)
            
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

    def deviation(self):
        return sum([abs(self.avg_size - b.size) for b in self.buckets])/self.avg_size

    def balance(self):
        # first get all the batches in a list
        batches = []

        # TODO maybe rework the whole thing so that we don't have to create a
        # new list?
        new_buckets = []
        for bucket in self.buckets:
            new_buckets.append(Bucket(bucket.name))
            for batch_name in bucket.batches:
                batches.append((batch_name, bucket.batches[batch_name]))


        # Sort the list of batches
        batches = sorted(batches, key = operator.itemgetter(1), reverse = True)

        
        added = True
        falses = [0]*len(new_buckets)
        left_overs = []
        # Now assign batches

    
        # Assign all the too-big batches first
        for i, batch in enumerate(batches):

            # Find the least-full bucket and assign this batch
            if batch[1] > self.avg_size:
                min_del = 10**7
                min_idx = -1

                # Find the lest-bad bucket
                for j, bucket in enumerate(new_buckets):
                    if (bucket.size + batch[1]) - self.avg_size < min_del:
                        min_idx = j
                        min_del = (bucket.size + batch[1]) - self.avg_size 

                # Now add to the least-bad bucket
                new_buckets[min_idx].add_batch(batch[0], batch[1])

            else:
                left_overs = batches[i:]
                break

        
        
        # Now iterate through remaining batches and add them to the bucket
        # that will be _least_ over the average
        for batch in left_overs:
            min_del = 10**7
            min_idx = -1

            # Find the lest-bad bucket
            for i, bucket in enumerate(new_buckets):
                if (bucket.size + batch[1]) - self.avg_size < min_del:
                    min_idx = i
                    min_del = (bucket.size + batch[1]) - self.avg_size 

            # Now add to the least-bad bucket
            new_buckets[min_idx].add_batch(batch[0], batch[1])

        return BucketList(new_buckets)

    def __gt__(self, other):
        return self.size > other.size

    def __repr__(self):
        return str(self.buckets)

    def pretty_print(self):
        for bucket in self.buckets:
            print(bucket.name, bucket.size)
            for batch in bucket.batches:
                print('\t', batch, bucket.batches[batch])
