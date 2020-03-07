#!/usr/bin/python2
# flake8: noqa
import random
from copy import deepcopy
import json
import sys
import time

if len(sys.argv) != 2:
    print "Usage {file} data.json".format(file=sys.argv[0])
    sys.exit(1)

# Reads data in format of dataForPlan.
with open(sys.argv[1]) as f:
    data = json.load(f)

workshops = {ws['wid']:ws for ws in data['workshops']}
workshops_per_block = len(workshops) / 6

points_not_allowed = 10**3
points_wrong_workshops_per_block = 10**4

verbose = False

users = {u['uid']: u for u in data['users']}
for uid in users.keys():
    users[uid]['part'] = set()
    users[uid]['blocks'] = set()
    del users[uid]['start']
    del users[uid]['end']
    users[uid]['blocks'].add(0)
    users[uid]['blocks'].add(1)
    users[uid]['blocks'].add(2)
    users[uid]['blocks'].add(3)
    users[uid]['blocks'].add(4)
    users[uid]['blocks'].add(5)

wid_list = list(workshops.keys())

for part in data['participation']:
    if part['wid'] in wid_list:
        users[part['uid']]['part'].add(part['wid'])

for ws in workshops.values():
    for lec_uid in ws['lecturers']:
        users[lec_uid]['part'].add(ws['wid'])


class Plan(object):
    def __init__(self, tab=None):
        if tab is None:
            self.blocks = [set() for i in xrange(6)]
            self.workshops = dict()
        else:
            self.blocks = [set() for i in xrange(6)]
            for i in xrange(6):
                for wid in tab[i]:
                    self.add(i, wid)
    
    def tab(self):
        tab = []
        for i in xrange(6):
            tab.append([])
            for wid in self.blocks[i]:
                tab[i].append(wid)
        return tab
    
    def add(self, block, wid):
        assert 0 <= block <= 5
        assert wid in workshops
        assert wid not in self.workshops
        self.blocks[block].add(wid)
        self.workshops[wid] = block
    
    def copy(self):
        plan = Plan()
        plan.blocks = deepcopy(self.blocks)
        plan.workshops = deepcopy(self.workshops)
        return plan
    
    def mutate(self, wid=None, block=None):
        if wid is None:
            random_wid = random.choice(wid_list)
        else:
            random_wid = wid
        if block is None:
            random_block = random.randint(0, 5)
        else:
            random_block = block
        while random_block == self.workshops[random_wid]:
            random_block = random.randint(0, 5)
        
        self.blocks[self.workshops[random_wid]].remove(random_wid)
        del self.workshops[random_wid]
        self.add(random_block, random_wid)
    
    def mutate_by_exchange(self):
        random_wid1 = random.choice(wid_list)
        random_wid2 = random.choice(wid_list)
        random_block1 = self.workshops[random_wid1]
        random_block2 = self.workshops[random_wid2]
        self.mutate(random_wid1, random_block2)
        self.mutate(random_wid2, random_block1)
        
    @staticmethod
    def make_random_plan():
        plan = Plan()
        for wid in workshops.keys():
            plan.add(random.randint(0, 5), wid)
        return plan
    
    def describe(self):
        for uid in users.keys():
            printed_user_already = False
            for block in users[uid]['blocks']:
                wids_on_block_for_user = [wid for wid in users[uid]['part'] if wid in self.blocks[block]]
                if len(wids_on_block_for_user) > 1:
                    if printed_user_already is False:
                        print " *", users[uid]['name'], " registered for", len(users[uid]['part']), "workshops"
                        printed_user_already = True
                    print "  ", len(wids_on_block_for_user), "collisions:", [workshops[wid]['name'] for wid in wids_on_block_for_user]
                    
        
        collision_sum = 0
        collision_user_sum = 0
        for block in xrange(6):
            print "BLOCK", block
            for wid in self.blocks[block]:
                participants_willing_to = 0
                participants_today = 0
                collisions = 0
                collision_users = 0
                for uid in users.keys():
                    if wid in users[uid]['part']:
                        participants_willing_to += 1
                        if block in users[uid]['blocks']:
                            participants_today += 1
                            collided = False
                            for wid2 in self.blocks[block]:
                                if wid2 == wid:
                                    continue
                                if wid2 in users[uid]['part']:
                                    if collided is False:
                                        collision_users += 1
                                        collision_user_sum += 1
                                        collided = True
                                    collisions += 1
                                    collision_sum += 1
                print " *", wid, workshops[wid]['name'], "-", [users[lid]['name'] for lid in workshops[wid]['lecturers']][0]
                print "   participants today/willing:", participants_today, "/", participants_willing_to
                print "   collisions / user collisions:", collisions, "/", collision_users
            print "-------"
        print "colisions total = {sum}, colision users total = {users}".format(sum=collision_sum, users=collision_user_sum)

    def evaluate(self, verbose=False):
        all_wids = set()
        for widset in self.blocks:
            all_wids.update(widset)
        
        for wid in wid_list:
            if wid not in all_wids:
                raise KeyError("There is no wid", wid, all_wids)
        
        points = 0
        points_col = 0
        
        for wid in all_wids:
            for lec_uid in workshops[wid]['lecturers']:
                if self.workshops[wid] not in users[lec_uid]['blocks']:
                    if verbose:
                        print "COLLISION OF LECTURER"
                        print "\tlec_uid={uid} wid={wid}".format(uid=lec_uid, wid=wid)
                    points -= 10**6

        for wid in all_wids:
            for disallowed_block in workshops[wid]['disallowed_blocks']:
                if wid in self.blocks[disallowed_block]:
                    if verbose:
                        print "DISALLOWED BLOCK"
                        print "\twid={wid} block={block}".format(wid=wid, block=disallowed_block), workshops[wid]['name']
                    points -= points_not_allowed

        for block in self.blocks:
            if abs(workshops_per_block - len(block)) > 0.9:
                if verbose:
                    print "WRONG NUMBER OF WORKSHOPS IN BLOCK {block}".format(block=block)
            points -= abs(workshops_per_block - len(block)) * points_wrong_workshops_per_block


        col_counter = {wid:0 for wid in all_wids}
        for uid in users.keys():
            user_blocks = dict()
            for wid in users[uid]['part']:
                if self.workshops[wid] in users[uid]['blocks']:
                    if self.workshops[wid] not in user_blocks:
                        user_blocks[self.workshops[wid]] = []
                    user_blocks[self.workshops[wid]].append(wid)
            for block in user_blocks.keys():
                if len(user_blocks[block]) > 1:
                    for wid in user_blocks[block]:
                        col_counter[wid] += 1
                    
            empty_blocks = min(len(users[uid]['blocks']), len(users[uid]['part'])) - len(user_blocks)
            assert empty_blocks >= 0
            #print empty_blocks, users[uid]['name']
            points -= empty_blocks**empty_blocks if empty_blocks>0 else 0
            if empty_blocks > 0:
                if verbose:
                    print empty_blocks, "EMPTY BLOCKS for", users[uid]['name']
                    print "\tuid={uid}".format(uid=uid)
            #points += len(user_blocks)
        
        for wid in col_counter.keys():
            points_col -= col_counter[wid]**2
        
        return points * 1 + points_col
        

# print workshops
# print
# print users

it_wid = 0
block = 0


def improve(plan, points):
    global it_wid
    global block
    plan2 = plan.copy()
    for i in xrange(random.randint(1, 2)):
        if random.randint(0, 1) == 0:
            plan2.mutate(wid_list[it_wid], block)
            it_wid += 1
            if it_wid >= len(wid_list):
                it_wid = 0
            block += 1
            if block >= 6:
                block = 0
        else:
            plan2.mutate_by_exchange()
    points2 = plan2.evaluate()
    if points2 >= points:
        plan = plan2
        points = points2
    return plan, points


pnp = [Plan.make_random_plan() for i in xrange(1000)]
pnp = [(plan, plan.evaluate()) for plan in pnp]

BEST = pnp[0][1]
last_print_time = 0

try:
    while True:
        for i in xrange(len(pnp)):
            pnp[i] = improve(pnp[i][0], pnp[i][1])
            if pnp[i][1] > BEST:
                BEST = pnp[i][1]
            if verbose:
                print BEST, pnp[i][1]
        if last_print_time < time.time() - 1.0:
            print BEST
            last_print_time = time.time()
        
except KeyboardInterrupt:
    print "ABORTED"

for i in xrange(len(pnp)):
    if pnp[i][1] == BEST:
        pnp[i][0].evaluate(True)
        pnp[i][0].describe()
        print "points:", pnp[i][1]
        print "TAB for later use:"
        print pnp[i][0].tab()
        break
