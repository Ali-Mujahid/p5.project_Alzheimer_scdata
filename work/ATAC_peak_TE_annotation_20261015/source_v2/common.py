"""Small, dependency-free interval and TSV utilities. BED coordinates are 0-based."""
import bisect
import csv
import gzip
import hashlib
from collections import defaultdict


def opener(path, mode="rt"):
    return gzip.open(path, mode) if str(path).endswith(".gz") else open(path, mode)


def table(path, required):
    with opener(path) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        yield from reader


def write_table(path, fields, rows):
    with opener(path, "wt") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class IntervalIndex:
    """Sorted starts + prefix-max ends avoid incorrect nested-interval searches."""
    def __init__(self, intervals):
        grouped = defaultdict(list)
        for chrom, start, end, payload in intervals:
            if not (0 <= start < end):
                raise ValueError(f"Invalid interval: {chrom}:{start}-{end}")
            grouped[chrom].append((start, end, payload))
        self.data = {}
        for chrom, values in grouped.items():
            values.sort(key=lambda x: (x[0], x[1]))
            starts, prefix, largest = [], [], -1
            for start, end, _ in values:
                starts.append(start)
                largest = max(largest, end)
                prefix.append(largest)
            self.data[chrom] = (values, starts, prefix)

    def overlap(self, chrom, start, end):
        if chrom not in self.data:
            return []
        values, starts, prefix = self.data[chrom]
        cursor = bisect.bisect_left(starts, end) - 1
        result = []
        while cursor >= 0 and prefix[cursor] > start:
            left, right, payload = values[cursor]
            if right > start and left < end:
                result.append((left, right, payload))
            cursor -= 1
        return result


def bh(pvalues):
    """Benjamini-Hochberg adjusted P values, preserving input order."""
    n = len(pvalues)
    order = sorted(range(n), key=lambda i: pvalues[i])
    output, running = [1.0] * n, 1.0
    for rank in range(n, 0, -1):
        idx = order[rank - 1]
        running = min(running, pvalues[idx] * n / rank)
        output[idx] = min(1.0, running)
    return output
