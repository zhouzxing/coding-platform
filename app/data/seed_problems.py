"""Seed problems.json with a few classic easy/medium problems."""
import json, os

BASE = os.path.dirname(__file__)
PROBLEMS = [
  {
    "id": 1,
    "title": "Two Sum",
    "difficulty": "Easy",
    "accept_rate": 55.2,
    "tags": ["Array", "Hash Map"],
    "description": """## 题目

给定一个整数数组 `nums` 和一个目标值 `target`，返回 `nums` 中和为 `target` 的两个数的**索引**（下标从 0 开始）。

每个输入只保证一个答案，且同一元素不能使用两次。

## 示例

**输入:** `nums = [2,7,11,15], target = 9`
**输出:** `[0,1]`  // 因为 nums[0] + nums[1] == 2 + 7 == 9
""",
    "signature": "def solve(nums: list[int], target: int) -> list[int]:",
    "test_cases": [
      {"input": {"nums": [2,7,11,15], "target": 9}, "expected": [0,1]},
    ],
    "hidden_tests": [
      {"input": {"nums": [3,2,4], "target": 6}, "expected": [1,2]},
      {"input": {"nums": [3,3], "target": 6}, "expected": [0,1]},
      {"input": {"nums": [1,2,3,4,5], "target": 9}, "expected": [3,4]},
      {"input": {"nums": [0,4,3,0], "target": 0}, "expected": [0,3]},
    ],
  },
  {
    "id": 2,
    "title": "Valid Anagram",
    "difficulty": "Easy",
    "accept_rate": 61.8,
    "tags": ["String", "Hash Map"],
    "description": """## 题目

给定两个字符串 `s` 和 `t`，判断 `t` 是否是 `s` 的**异位词**（字母相同但顺序不同）。

## 示例

**输入:** `s = "anagram", t = "nagaram"`
**输出:** `true`
""",
    "signature": "def solve(s: str, t: str) -> bool:",
    "test_cases": [
      {"input": {"s": "anagram", "t": "nagaram"}, "expected": True},
    ],
    "hidden_tests": [
      {"input": {"s": "rat", "t": "car"}, "expected": False},
      {"input": {"s": "", "t": ""}, "expected": True},
      {"input": {"s": "a", "t": "ab"}, "expected": False},
    ],
  },
  {
    "id": 3,
    "title": "Maximum Subarray",
    "difficulty": "Medium",
    "accept_rate": 49.3,
    "tags": ["Array", "Dynamic Programming"],
    "description": """## 题目

给定一个整数数组 `nums`，找到一个具有最大和的**连续子数组**，返回该和。

## 示例

**输入:** `nums = [-2,1,-3,4,-1,2,1,-5,4]`
**输出:** `6`  // 连续子数组 `[4,-1,2,1]` 的和最大
""",
    "signature": "def solve(nums: list[int]) -> int:",
    "test_cases": [
      {"input": {"nums": [-2,1,-3,4,-1,2,1,-5,4]}, "expected": 6},
    ],
    "hidden_tests": [
      {"input": {"nums": [1]}, "expected": 1},
      {"input": {"nums": [5,4,-1,7,8]}, "expected": 23},
      {"input": {"nums": [-1,-2,-3,-4]}, "expected": -1},
      {"input": {"nums": [1,2,3,4,5]}, "expected": 15},
    ],
  },
  {
    "id": 4,
    "title": "Two Sum II (Sorted Array)",
    "difficulty": "Medium",
    "accept_rate": 58.4,
    "tags": ["Array", "Two Pointers"],
    "description": """## 题目

给定一个**已排序**的整数数组 `numbers`（升序），返回两个数的**下标**（1-indexed），使它们之和等于 `target`。

## 示例

**输入:** `numbers = [2,7,11,15], target = 9`
**输出:** `[1,2]`  // 1-indexed
""",
    "signature": "def solve(numbers: list[int], target: int) -> list[int]:",
    "test_cases": [
      {"input": {"numbers": [2,7,11,15], "target": 9}, "expected": [1,2]},
    ],
    "hidden_tests": [
      {"input": {"numbers": [2,3,4], "target": 6}, "expected": [1,3]},
      {"input": {"numbers": [-1,0], "target": -1}, "expected": [1,2]},
    ],
  },
  {
    "id": 5,
    "title": "Reverse Linked List (values)",
    "difficulty": "Easy",
    "accept_rate": 62.5,
    "tags": ["Linked List", "Array"],
    "description": """## 题目

给定一个整型数组 `head` 表示链表的节点值序列（从左到右），实现链表反转后返回节点值的**逆序**列表。

**输入:** `head` 是节点值列表，**输出** 是反转后的节点值列表。

> 说明: 由于沙箱内不构造实际 `ListNode` 对象，本题接受纯列表输入；解题时你可以按链表反转思路遍历，或直接返回逆序。

## 示例

**输入:** `head = [1,2,3,4,5]`
**输出:** `[5,4,3,2,1]`
""",
    "signature": "def solve(head: list[int]) -> list[int]:",
    "test_cases": [
      {"input": {"head": [1,2,3,4,5]}, "expected": [5,4,3,2,1]},
    ],
    "hidden_tests": [
      {"input": {"head": []}, "expected": []},
      {"input": {"head": [1]}, "expected": [1]},
      {"input": {"head": [1,2]}, "expected": [2,1]},
    ],
  },
  {
    "id": 6,
    "title": "Binary Search",
    "difficulty": "Easy",
    "accept_rate": 63.1,
    "tags": ["Array", "Binary Search"],
    "description": """## 题目

给定一个升序排列的整数数组 `nums` 和目标值 `target`，在数组中找到 `target`，返回其下标；若不存在，返回 `-1`。

要求时间复杂度 O(log n)。

## 示例

**输入:** `nums = [-1,0,3,5,9,12], target = 9`
**输出:** `4`
""",
    "signature": "def solve(nums: list[int], target: int) -> int:",
    "test_cases": [
      {"input": {"nums": [-1,0,3,5,9,12], "target": 9}, "expected": 4},
    ],
    "hidden_tests": [
      {"input": {"nums": [-1,0,3,5,9,12], "target": 2}, "expected": -1},
      {"input": {"nums": [5], "target": 5}, "expected": 0},
      {"input": {"nums": [5], "target": 6}, "expected": -1},
    ],
  },
]

if __name__ == "__main__":
    out = os.path.join(BASE, "problems.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(PROBLEMS, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(PROBLEMS)} problems to {out}")
