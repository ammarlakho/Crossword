import sys
import random
from crossword import *
from queue import Queue
import time


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.crossword.variables:
            words = self.domains[var].copy()
            for word in words: 
                if len(word) != var.length:
                    self.domains[var].remove(word)
        
        
    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        
        overlap = self.crossword.overlaps[x, y]
        if overlap is not None:
            atleastOneRevision = False
            xwords = self.domains[x].copy()
            ywords = self.domains[y].copy()
            for xword in xwords:
                xcommon = xword[overlap[0]]
                revision = True
                for yword in ywords:
                    ycommon = yword[overlap[1]]
                    if xcommon == ycommon:
                        revision = False

                if revision:
                    self.domains[x].remove(xword)
                    atleastOneRevision = True

            return atleastOneRevision
        return False

            

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue = Queue(0)

        if arcs is not None:
            for arc in arcs:
                queue.put(arc)
        else:
            for var in self.crossword.variables:
                neighbors = self.crossword.neighbors(var)
                for neighbor in neighbors:
                    arc = (var, neighbor)
                    queue.put(arc)

        while not queue.empty():
            arc = queue.get()
            X = arc[0]
            Y = arc[1]
            if self.revise(X, Y):
                if len(self.domains[X]) == 0:
                    return False

                for Z in self.crossword.neighbors(X):
                    if(Z != Y):
                        arc = (Z, X)
                        queue.put(arc)
                    
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return len(assignment) == len(self.crossword.variables)
        

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        distinct = list()
        
        for var in assignment:
            if assignment[var] in distinct:
                return False
            if len(assignment[var]) != var.length:
                return False
            
            for neighbor in self.crossword.neighbors(var):
                arc = self.crossword.overlaps[var, neighbor]
                if neighbor in assignment:
                    if assignment[var][arc[0]] != assignment[neighbor][arc[1]] :
                        return False
            
            distinct.append(assignment[var])
        return True
            

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
                
        values_Dict = list()
        for value in self.domains[var]:
            cost = 0
            for neighbor in self.crossword.neighbors(var):
                if neighbor not in assignment:
                    for neighbor_value in self.domains[neighbor]:
                        if neighbor_value == value:
                            cost += 1
            value_dict = {'value': value, 'cost': cost}
            values_Dict.append(value_dict) 

        values = list()
        values_Dict.sort(key=self.get_cost, reverse=True)
        
        for dict_v in values_Dict:
            values.append(dict_v['value'])
        
        return values


        
    def get_cost(self, values_dict):
        return values_dict['cost']

    def get_mrv(self, variables_Dict):
        return variables_Dict['mrv']
    def get_degree(self, variables_Dict):
        return variables_Dict['degree']


    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        variables_old = list(self.crossword.variables)
        variables_new = list(self.crossword.variables)

        for var in variables_old:
            for key in assignment.keys():
                if var == key:
                    variables_new.remove(var)

        variables = list()
        for var in variables_new:
            mrv = len(self.domains[var])
            degree = len(self.crossword.neighbors(var))
            varDict = {'var': var , 'mrv': mrv, 'degree': degree}
            variables.append(varDict) 

        variables.sort(key=self.get_mrv)

        # Only 1 possibility
        if len(variables) == 1:
            return variables[0]['var']
        # More possibilities but NO ties
        if variables[0]['mrv'] != variables[1]['mrv']:
            return variables[0]['var']
        # Ties
        variables_tied = [variables[0]]
        for i in range(len(variables) - 1):
            if variables[i]['mrv'] == variables[i+1]['mrv']:
                variables_tied.append(variables[i+1])
        
        variables_tied.sort(key=self.get_degree, reverse=True)
        
        return variables_tied[0]['var']




        
    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assignment[var] = value
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result is not None:
                    return result
            del assignment[var]
            
        return None



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()
    
    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)

    


if __name__ == "__main__":
    main()


