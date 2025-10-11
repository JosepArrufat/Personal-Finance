from __future__ import annotations
from typing import Dict, List, Literal, Optional, Mapping
import os
import json
import pandas as pd

Scope = Literal["categories", "income_categories"]

class CategoryStore:
    def __init__(self, categories_path: str, income_categories_path: str):
        self.paths = {
            "categories": categories_path,
            "income_categories": income_categories_path
        }
        self.data: Dict[Scope, Dict[str, List[str]]] = {
            "categories": {"uncategorized": []},
            "income_categories": {"uncategorized": [],}
        }
        self.lookups: Dict[Scope, Dict[str, str]] = {
            "categories": {},
            "income_categories": {},
        }
        self._dirty: bool = False
        self._loaded: bool = False
    def load_all(self) -> None:
        for scope, path in self.paths.items():
            if not os.path.exists(path):
                try:
                    with open(path, "w") as f:
                        json.dump(self.data[scope], f)
                except IOError as e:
                    print(f"Error creating {scope} file: {e}")
            try:
                with open(path, "r") as f:
                    loaded_data = json.load(f)
                    norm = {}
                    for cat, details in loaded_data.items():
                        c = self.normalize_category(cat)
                        norm[c] = [self.normalize_detail(d) for d in details]
                    if "uncategorized" not in norm:
                        norm["uncategorized"] = []
                    self.data[scope] = norm
            except IOError as e:
                print(f"Error creating {scope} file: {e}")
        self.rebuild_lookups()
        self._loaded = True  
    def is_loaded(self) -> bool:
        return self._loaded             
    def save_all(self) -> None:
        if not self._dirty:
            return
        else:
            try:
                for cat, path in self.paths.items():
                    with open(path, "w") as f:
                        json.dump(self.data[cat], f)
                self._dirty = False
            except IOError as e:
                print(f"Error creating {cat} file: {e}")
    def get_options(self, scope: Scope) -> List[str]:
        return sorted(self.data[scope].keys())
    def get_lookup(self, scope: Scope) -> Mapping[str, str]:
        return dict(self.lookups[scope])
    def get_data(self, scope: Scope) -> Dict[str, List[str]]:
        return {k:list(v) for k, v in self.data[scope].items()}
    def add_category(self, scope: Scope, name:str) -> None:
        c = self.normalize_category(name)
        if c not in self.data[scope]:
            self.data[scope][c] = []
            self._dirty = True
    def apply_edits(
            self,
            scope: Scope,
            edited_rows: Dict[int, Dict[str, object]],
            current_df: "pd.DataFrame",
    ) -> None:
        for rw_idx, row_changes in edited_rows.items():
            if "Category" not in row_changes:
                continue
            row_index_int = int(rw_idx)
            detail = self.normalize_detail(current_df.iloc[row_index_int]["Details"])
            new_category = self.normalize_category(row_changes["Category"])
            old_category = self.lookups[scope].get(detail)
            if old_category and detail in self.data[scope].get(old_category):
                self.data[scope][old_category].remove(detail)
            if new_category not in self.data[scope]:
                self.data[scope][new_category] = []
            if detail not in self.data[scope][new_category]:
                self.data[scope][new_category].append(detail)
            self.lookups[scope][detail] = new_category
            self._dirty = True

    def rebuild_lookups(self)->None:
        for categorie in self.data.keys():
            self.lookups[categorie].clear()
            for cat, detail in self.data[categorie].items():
                for d in detail:
                    self.lookups[categorie][d] = cat

    @staticmethod
    def normalize_category(name: str) -> str:
        return (name or "").strip().lower()

    @staticmethod
    def normalize_detail(text: str) -> str:
        return (text or "").strip().lower()