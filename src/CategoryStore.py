from __future__ import annotations
import hashlib
from typing import Dict, List, Literal, Optional, Mapping
import os
import json
import pandas as pd

Scope = Literal["categories", "income_categories"]

class CategoryStore:
    def __init__(self, categories_path: str, income_categories_path: str, tags_path="tags.json"):
        self.paths = {
            "categories": categories_path,
            "income_categories": income_categories_path,
            "tags": tags_path
        }
        self.data: Dict[Scope, Dict[str, List[str]]] = {
            "categories": {"uncategorized": []},
            "income_categories": {"uncategorized": [],}
        }
        self.lookups: Dict[Scope, Dict[str, str]] = {
            "categories": {},
            "income_categories": {},
        }
        self.tags: Dict[str, Dict[str, List[str]]] = {}
        self.current_file: Optional[str] = None
        self._dirty: bool = False
        self._tags_dirty: bool = False
        self._loaded: bool = False
    def load_all(self) -> None:
        for scope in ["categories", "income_categories"]:
            path = self.paths[scope]
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
        tags_path = self.paths["tags"]
        if not os.path.exists(tags_path):
            try:
                with open(tags_path, "w") as f:
                    json.dump({}, f)
            except IOError as e:
                print(f"Error creating tags file: {e}")
        else:
            try:
                with open(tags_path, "r") as f:
                    self.tags = json.load(f)
            except IOError as e:
                print(f"Error reading tags file: {e}")
        self.rebuild_lookups()
        self._loaded = True  
    def is_loaded(self) -> bool:
        return self._loaded             
    def save_all(self) -> None:
        if self._dirty:
            try:
                for cat, path in self.paths.items():
                    with open(path, "w") as f:
                        json.dump(self.data[cat], f)
                self._dirty = False
            except IOError as e:
                print(f"Error creating {cat} file: {e}")
        if self._tags_dirty:
            try:
                with open(self.paths["tags"], "w") as f:
                    json.dump(self.tags, f)
                self._tags_dirty = False
            except IOError as e:
                print("Error saving tags file: {e}")
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
    
    def set_current_file(self, filename: str) -> None:
        self.current_file = filename
        if filename not in self.tags:
            self.tags[filename] = {}
    
    def create_transaction_id(self, row: pd.Series) -> str:
        key_parts = [
            str(row.get("Date", "")),
            str(row.get("Details", "")),
            str(row.get("Amount", "")),
            str(row.get("Description", "")),
        ]
        key = "|".join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def get_tags(self, transaction_id: str) -> List[str]:
        return self.tags.get(self.current_file, {}).get(transaction_id, [])
    def set_tags(self, transaction_id: str, tags: List[str]):
        if self.current_file is None:
            raise ValueError("No specified file")
        if self.current_file not in self.tags:
            self.tags[self.current_file] = {}
        self.tags[self.current_file][transaction_id] = tags
        self._tags_dirty = True
    def add_tags(self, tag: str, transaction_id: str):
        tag_normalized = tag.strip().lower()
        current_tags = self.get_tags(transaction_id)
        if tag_normalized and tag_normalized not in current_tags:
            current_tags.append(tag_normalized)
            self.set_tags(self, transaction_id, current_tags)
    def remove_tag(self, tag: str, transaction_id: str):
        current_tags = self.get_tags(transaction_id)
        tag_normalized = tag.strip().lower()
        if tag_normalized in current_tags:
            current_tags.remove(tag_normalized)
            self.set_tags(transaction_id, current_tags)
    def get_all_tags(self) -> List[str]:
        if self.current_file is None:
            return []
        all_tags = set()
        for tag in self.tags.get(self.current_file, {}).values():
            all_tags.append(tag)
        return sorted(all_tags)
    def apply_tags_to_df(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        self.set_current_file(filename)
        df = df.copy()
        df["transaction_id"] = df.apply(self.create_transaction_id, axis=1)
        df["tags"] = df["transaction_id"].apply(self.get_tags)
        return df
    def apply_tag_edits(
            self,
            edited_rows: Dict[int, Dict[str, object]],
            current_df: "pd.Dataframe",
    )->None:
        for rw_idx, row_canges in edited_rows.items():
            if "tags" not in edited_rows.items():
                continue
            row_idx_int = int(rw_idx)
            transaction_id = current_df.ilos[row_idx_int]["transaction_id"]
            new_tags = row_canges["tags"]
            if isinstance(new_tags, str):
                new_tags = [t.strip().lower() for t in new_tags.split(',') if t.strip()]
            elif isinstance(new_tags, list):
                new_tags = [str(t).strip().lower() for t in new_tags if str(t).strip()]
            else:
                new_tags = []
            self.set_tags(transaction_id, new_tags)
    @staticmethod
    def normalize_category(name: str) -> str:
        return (name or "").strip().lower()

    @staticmethod
    def normalize_detail(text: str) -> str:
        return (text or "").strip().lower()