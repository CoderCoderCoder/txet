import cmd
import random
import re

DEBUG_MODE = False

PRIORITY = 0
LOOKED_AT = 1

def newNoun():
    # (priority, looked at)
    # Nouns come in with priority 1, decay over time.
    return [1, False]

def loadVerbs():
    with open('verbs.txt') as f:
        verbs = f.readlines()
    return [v[:-1] for v in verbs]

def lowestPriority(nouns):
    min_priority = 0
    worst_noun = None
    for n in nouns:
        if nouns[n][PRIORITY] < min_priority:
            min_priority = nouns[n][PRIORITY]
            worst_noun = n
    return worst_noun

def highest_priority(nouns):
    max_priority = 0
    best_noun = None
    for n in nouns:
        if nouns[n][PRIORITY] > max_priority:
            max_priority = nouns[n][PRIORITY]
            best_noun = n
    return best_noun

def compilePattern(filename):
    with open(filename) as f:
        lines = f.readlines()
    substitutions = {}
    if len(lines) > 3:
        for line in lines[4:]:
            i = line.find('}')
            substitutions[line[:i+1]] = line[i+2:-1]
    expression = lines[0][:-1]
    for s in substitutions.keys():
        expression = re.sub(s, substitutions[s], expression)
    return expression

class Location:
    north = None
    east = None
    south = None
    west = None
    nouns = {}

class Shell(cmd.Cmd):
    intro = "Txet: A reverse text adventure by Adam Sattaur (Nobody)." + \
            "\n\nFor help, type 'help'." + \
            "\n\nUse a blank line to allow the player to act." + \
            "\nStart a line with 'The End.' to exit."
    prompt = '\n'

    current_description = ''

    verbs = ['look',
            'examine',
            'use',
            'wait',
            'inventory',
            'go']*2 + loadVerbs()

    noun_pattern = compilePattern('noun.pattern')
    ideal_memory = 7;

    location = Location()

    # Nouns are in the form "priority, looked at"
    nouns = {}

    def respond(self, text):
        # Make everything lowercase just to be consistent.
        text = text.lower()
        # Any nouns mentioned get more priority
        for noun in self.nouns:
            if noun in text:
                if self.nouns[noun][PRIORITY] < 0:
                    self.nouns[noun][PRIORITY] = 1
                self.nouns[noun][PRIORITY] += 1
        # Check for compass directions
        if 'north' in text and not self.location.north:
            l = Location()
            self.location.north = l
            l.south = self.location
        if 'east' in text and not self.location.east:
            l = Location()
            self.location.east = l
            l.west = self.location
        if 'south' in text and not self.location.south:
            l = Location()
            self.location.south = l
            l.north = self.location
        if 'west' in text and not self.location.west:
            l = Location()
            self.location.west = l
            l.east = self.location
        # Analyse nouns
        n = re.findall(self.noun_pattern, text, re.I)
        # Pick out new nouns and add to list
        for noun in n:
            noun = noun.strip()
            for nn in self.nouns:
                if noun.startswith(nn):
                    noun = nn
            if noun not in self.nouns:
                self.nouns[noun] = newNoun();
        # Update noun correlations
        # Priority decay
        for n in self.nouns:
            self.nouns[n][PRIORITY] -= random.random()
        # Drop bottom of list
        if len(self.nouns) > self.ideal_memory:
            # Find least important noun
            worst_noun = lowestPriority(self.nouns)
            if worst_noun:
                del self.nouns[worst_noun]

        if DEBUG_MODE:
            print("I know about the following:")
            for n in self.nouns:
                print(n, self.nouns[n][PRIORITY])

        # Now decide on what to do. For now let's pick a verb from the list and
        # just do that.
        best_noun = highest_priority(self.nouns)
        verb = random.choice(self.verbs)
        if best_noun == None:
            # We can only look, wait, go and inventory
            possible_verbs = ['look', 'wait', 'inventory']
            if self.location.north or self.location.east \
                or self.location.south or self.location.west:
                possible_verbs.append('go')
            verb = random.choice(possible_verbs)
        if verb == 'use':
            # With 50% chance, pick another noun
            if len(self.nouns) > 1 and random.choice([0,1]) == 1:
                other_noun = best_noun
                while(other_noun == best_noun):
                    other_noun = random.choice(list(self.nouns.keys()))
                print(">use {} on {}".format(best_noun, other_noun))
                return
            print(">use {}".format(best_noun))
        elif verb == 'look' or verb == 'examine':
            # Check that we haven't looked at everything
            if (self.looked_at_everything() or best_noun == None):
                print(">look")
                return
            while(self.nouns[best_noun][LOOKED_AT]):
                best_noun = random.choice(list(self.nouns.keys()))
            print(">{} {}".format(verb, best_noun))
            self.nouns[best_noun][LOOKED_AT] = True;
            return
        elif verb == 'wait':
            print(">wait")
            return
        elif verb == 'inventory':
            print(">inventory")
            return
        elif verb == 'go':
            # Which way?
            possible_directions = []
            if self.location.north:
                possible_directions.append('north')
            if self.location.east:
                possible_directions.append('east')
            if self.location.south:
                possible_directions.append('south')
            if self.location.west:
                possible_directions.append('west')
            if len(possible_directions) == 0:
                print(">look")
                return
            direction = random.choice(possible_directions)
            print(">go {}".format(direction))
            if direction == 'north':
                self.location = self.location.north
            if direction == 'east':
                self.location = self.location.east
            if direction == 'south':
                self.location = self.location.south
            if direction == 'west':
                self.location = self.location.west
        else:
            print(">{} {}".format(verb, best_noun))

    def looked_at_everything(self):
        for n in self.nouns:
            if not self.nouns[n][LOOKED_AT]:
                return False
        return True

    def default(self, arg):
        self.current_description += arg

    def do_help(self, arg):
        print("This is an experiment in interactive storytelling, based on "
            "text adventure games. You provide the adventure, and the computer "
            "will act basically at random."
            "\n\nAs an example, try typing something like: "
            "\n'You find yourself in a small room. There is a key on a table, "
            "and a door to the north.'"
            "\nYou can write as many paragraphs (lines) as you like. Pressing "
            "return on a blank line will allow the computer to act."
            "\n\nEnd your adventure by writing 'The End.' on its own line. "
            "You can write more on the same line, but the adventure will end "
            "after you press return.")

    def do_the(self, arg):
        self.do_The(arg)

    def do_The(self, arg):
        if (arg.lower().startswith('end.')):
            exit()
        else:
            self.default('The ' + arg)

    def emptyline(self):
        self.respond(self.current_description)
        self.current_description = ''

if __name__ == '__main__':
    Shell().cmdloop()
().cmdloop()
