#!/usr/bin/env python3
import inspect
import sys
sys.path.insert(0, "src")

from controllers.SliderMixin import SliderMixin
from controllers.ImageGalleryMixin import ImageGalleryMixin
from controllers.SearchMixin import SearchMixin
from controllers.DetailMixin import DetailMixin
from controllers.QueueMixin import QueueMixin
from controllers.InstalledMixin import InstalledMixin

def get_class_methods(cls):
    return {name for name, val in cls.__dict__.items() if callable(val) and not name.startswith("__")}

mixins = [SliderMixin, ImageGalleryMixin, SearchMixin, DetailMixin, QueueMixin, InstalledMixin]
all_mixin_methods = set()
for m in mixins:
    methods = get_class_methods(m)
    print(f"{m.__name__}: {len(methods)} methods")
    overlap = all_mixin_methods.intersection(methods)
    if overlap:
        print(f"  WARNING: Overlap in {m.__name__}: {overlap}")
    all_mixin_methods.update(methods)

print(f"\nTotal unique mixin methods: {len(all_mixin_methods)}")
