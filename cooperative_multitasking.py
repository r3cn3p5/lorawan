# Copyright (C) 2018, 2019 Andreas Motzek andreas-motzek@t-online.de
#
# This file is part of the Cooperative Multitasking package.
#
# You can use, redistribute and/or modify this file under the terms of the Modified Artistic License.
# See http://simplysomethings.de/open+source/modified+artistic+license.html for details.
#
# This file is distributed in the hope that it will be useful, but without any warranty; without even
# the implied warranty of merchantability or fitness for a particular purpose.

import utime
import gc
 
class Task:
    def __init__(self, when, priority, continuation, guard = None, duration = 0):
        self.when = when
        self.priority = priority
        self.continuation = continuation
        self.guard = guard
        self.siblings = []
        if not guard is None:
            self.duration = duration
            self.remaining = duration

class Tasks:
    def __init__(self, cycle = 30):
        self.heap = [None]
        self.count = 0
        self.cycle = cycle  # milliseconds
        self.current = utime.ticks_ms()

    def now(self, continuation, priority = 0):
        task = Task(self.current, priority, continuation)
        self._add(task)
        return task

    def after(self, duration, continuation, priority = 0):
        task = Task(utime.ticks_add(self.current, int(duration)), priority, continuation)
        self._add(task)
        return task

    def when_for_then(self, guard, duration, continuation, priority = 0):
        task = Task(self.current, priority, continuation, guard, int(duration))
        self._add(task)
        return task

    def when_then(self, guard, continuation, priority = 0):
        return self.when_for_then(guard, 0, continuation, priority)

    def only_one_of(self, task1, task2, task3 = None, task4 = None):
        if task4 is None and task3 is None:
            task1.siblings = [task1, task2]
            task2.siblings = task1.siblings
        elif task4 is None:
            task1.siblings = [task1, task2, task3]
            task2.siblings = task1.siblings
            task3.siblings = task1.siblings
        else:
            task1.siblings = [task1, task2, task3, task4]
            task2.siblings = task1.siblings
            task3.siblings = task1.siblings
            task4.siblings = task1.siblings

    def available(self):
        return self.count > 0

    def clear(self):
        self.heap = [None]
        self.count = 0

    @staticmethod
    def _ticks_max(ticks1, ticks2):
        return ticks1 if utime.ticks_diff(ticks1, ticks2) >= 0 else ticks2

    def run(self):
        if not self.available():
            return
        self._wait()
        self._mark_due_tasks()
        task = self._extract_ready_task()
        if task is not None:
            self._cancel_siblings(task)
            task.continuation()

    def _wait(self):
        self.current = self._ticks_max(self.current, utime.ticks_ms())
        task = self.heap[1]
        if utime.ticks_diff(self.current, task.when) < 0:
            gc.collect()
            utime.sleep_ms(utime.ticks_diff(task.when, self.current))
            self.current = self._ticks_max(task.when, utime.ticks_ms())

    def _mark_due_tasks(self):
        tasks = []
        while self.count > 0:
            task = self._extract(1)
            if utime.ticks_diff(self.current, task.when) >= 0:
                task.when = self.current  # all due tasks get the same timestamp
                tasks.append(task)
            else:
                self._add(task)
                break
        for task in tasks:
            self._add(task)  # now the tasks are sorted by priority

    def _extract_ready_task(self):
        task = self._extract(1)
        guard = task.guard
        if guard is None:
            return task
        result = guard()
        if result:
            if task.remaining <= self.cycle:
                return task
            task.remaining -= self.cycle
        else:
            task.remaining = task.duration
        task.when = utime.ticks_add(self.current, self.cycle)
        self._add(task)
        return None

    def _cancel_siblings(self, task):
        for sibling in task.siblings:
            if not task is sibling:
                self._remove(sibling)

    def _add(self, task):
        self.count += 1
        if len(self.heap) == self.count:
            self.heap.append(task)
        else:
            self.heap[self.count] = task
        self._bottom_up(self.count)

    def _extract(self, i):
        if self._is_outside(i):
            return None
        task = self.heap[i]
        self._top_down(i)
        return task

    def _remove(self, task):
        i = self._find(task)
        if self._is_inside(i):
            self._top_down(i)

    def _find(self, task, i = 1):
        while not self._is_leaf(i):
            if self.heap[i] is task:
                return i
            if self._is_before(task, self.heap[i]):
                return 0
            r = self._right_child(i)
            if self._is_inside(r):
                j = self._find(task, r)
                if self._is_inside(j):
                    return j
            i = self._left_child(i)
        if self.heap[i] is task:
            return i
        return 0

    def _bottom_up(self, i):
        while self._has_parent(i):
            p = self._parent(i)
            if self._is_before(self.heap[i], self.heap[p]):
                task = self.heap[i]
                self.heap[i] = self.heap[p]
                self.heap[p] = task
                i = p
            else:
                return

    def _top_down(self, i):
        while not self._is_leaf(i):
            l = self._left_child(i)
            r = self._right_child(i)
            if self._is_inside(r) and self._is_before(self.heap[r], self.heap[l]):
                self.heap[i] = self.heap[r]
                i = r
            else:
                self.heap[i] = self.heap[l]
                i = l
        if i == self.count:
            self.heap[i] = None
            self.count -= 1
        else:
            self.heap[i] = self.heap[self.count]
            self.heap[self.count] = None
            self.count -= 1
            self._bottom_up(i)

    @staticmethod
    def _is_before(task1, task2):
        if task1.when < task2.when:
            return True
        if task1.when == task2.when and task1.priority > task2.priority:
            return True
        return False

    def _is_outside(self, i):
        return i < 1 or i > self.count

    def _is_inside(self, i):
        return i >= 1 and i <= self.count

    def _is_leaf(self, i):
        return i > (self.count >> 1)

    @staticmethod
    def _has_parent(i):
        return i > 1

    @staticmethod
    def _parent(i):
        return i >> 1

    @staticmethod
    def _left_child(i):
        return i << 1

    @staticmethod
    def _right_child(i):
        return (i << 1) + 1
