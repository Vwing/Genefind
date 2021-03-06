#mutations:
#dshift by [val={1,3}]
#drandom delete 1
#drandom delete 3 consecutive
#drandom delete 3 random (essentially RD1 three times)
#drandom add 1
#drandom add 3 consecutive
#drandom add 3 random
#drandom switch

from argparse import ArgumentParser
import multiprocessing
import random
import statistics
import json
import pprint
import cProfile
import time
import pdb

#interesting functions:
#random.randrange()
#random.choice()
#random.choices()
#random.sample()

#algo
#input = a list of strings of ACTG seq
#output = a list of a list of 100 strings of mutated ACTG seq
#If the total number of mutations applied to the total number of input strings
#is less than 100, begin using output strings as input strings, in the order
#they were written.

#(???)
actg = "ACTG"

def random_delete_n(stringIn, n=1, consecutive=False):
    """Randomly delete n characters from a string."""
    stringOut = stringIn
    if len(stringOut)<n+1: return stringOut
    if not consecutive:
        for i in range(n):
            counter = random.randrange(len(stringOut))
            stringOut = stringOut[:counter]+stringOut[counter+1:]
        return stringOut
    else:
        counter = random.randrange((len(stringOut)-n+1))
        stringOut = stringOut[:counter]+stringOut[counter+n:]
        return stringOut

def random_add_n(stringIn, n=1, consecutive=False):
    """Randomly add n characters to a string."""
    stringOut = stringIn
    if len(stringOut)<n+1: return stringOut
    if not consecutive:
        for i in range(n):
            counter = random.randrange((len(stringOut)))
            stringOut = stringOut[:counter]+random.choice(actg)\
                        +stringOut[counter:]
        return stringOut
    else:
        counter = random.randrange((len(stringOut)-n+1))
        for i in range(n):
            stringOut = stringOut[:counter]+random.choice(actg)\
                        +stringOut[counter:]
        return stringOut

def RS(stringIn):
    stringOut = stringIn
    if len(stringOut)<2: return stringOut
    ct1 = random.randrange((len(stringOut)))
    ct2 = random.randrange((len(stringOut)))
    if ct1>ct2: ct2, ct1 = ct1, ct2
    stringOut = stringOut[:ct1]\
                +stringOut[ct2:ct2+1]\
                +stringOut[ct1+1:ct2]\
                +stringOut[ct1:ct1+1]\
                +stringOut[ct2+1:]
    return stringOut

def random_shift(stringIn, n):
    """Deterministically shift a string starting from position n.

    It's important to note that how this function is used in the rest of the program
    relies on you specifying constant values for the random shifts, so in the 
    set of possible random operations positions are defined such that it can be 
    1 or 3, positive or negative. This allows it to implement shifting both sides
    of the string in both lengths with one function."""
    if len(stringIn)<n+1: return stringIn
    stringOut = stringIn[n:]+stringIn[:n]
    return stringOut


# This might be confusing. Basically we're defining these operations in the global
# scope, and then executing them using eval(). This is about 1/3 slower than a native
# function call btw according to cProfiler.
operations = ["random_shift(string,3)","random_shift(string,1)","random_shift(string,-1)",
              "random_shift(string,-3)", "RS(string)",
              "random_add_n(string)","random_add_n(string,3)","random_add_n(string,3,True)",\
              "random_delete_n(string)","random_delete_n(string,3)","random_delete_n(string,3,True)"]

def Mod2Run(listIn, population):##pop gen
    """Generate the population. Here we randomly pull from a set of predefined
    operations to mutate our existing strings, then execute the operation."""
    #listIn = [a,b]
    mutCount = 0
    countProc = 0
    listOut = []
    listOut += listIn
    while len(listOut)<=population:
        string = listOut[countProc]
        op = random.choice(operations)
        listOut.append(eval(op))
        countProc+=1
    return listOut

def Mod3Run(string1, string2):##string comparison
    if len(string1)<2: return 0.0
    difference = sum(1 if x == y else 0 for x, y in \
                     zip(string1, string2)) \
                     * 100 / len(string2)
    lengthDif = min(len(string1)/len(string2),len(string2)/len(string1))
    difference *= lengthDif
    return difference

def Mod4Run(listIn, fitness, fitness_percentile):##pop cull
    listP = []
    for i in listIn:
        listP.append([Mod3Run(i,fitness),i])
    listP.sort()
    fitness_cutoff = -round(len(listP) * fitness_percentile)
    if not fitness_cutoff: # Handle case where we round to zero
        fitness_cutoff = 1
    return [candidate for candidate in reversed(listP[fitness_cutoff:])]

def Mod1Run(listIn, trackIn={}):##iterator
    trackOut = trackIn
    bestE = listIn[0]
    listOut = []
    if len(listIn) == 1:
        return listIn, trackOut
    for i in listIn:
        listOut.append(i[1])
    
    trackOut["lastFit"] = trackOut["currentFit"]
    trackOut["currentFit"] = bestE[0]
    trackOut["generationCount"]+=1
    bestFit = trackOut["bestFit"]
    if bestFit<bestE[0]:
        trackOut["bestFit"]=bestE[0]
    if bestE[0] == 100:
        print("Result Found.","\n"\
              ,"Generation count =", trackOut["generationCount"], '\n'\
              ,"String :\n", bestE[1])
        return listOut, trackOut
    return listOut, trackOut

def initial(initial_string_size):
    output = ''
    for i in range(initial_string_size):
        output+=random.choice(actg)
    return output

##base program
print("Modules loaded.")
print(\
    """
********************
"GeneFind: A Designspace Searcher"
********************
""")


def run_genefind(target_string, fitness_percentile, population, initial_string_size):
    """Run one instance of the genefind algorithm and return the number of 
    generations to find the target string."""
    lis = [initial(initial_string_size)]
    fitness = target_string
    fitness_cutoff = (100 - fitness_percentile) / 100
    track = {"generationCount":0, 'currentFit':0.0, \
             'lastFit':0.0, 'bestFit':0.0}
    while 1:
        lis, track = Mod1Run(lis, track)
        lis = Mod2Run(lis, population)
        lis = Mod4Run(lis,fitness, fitness_cutoff)
        if track["bestFit"] == 100:
            break
        if track["generationCount"]%1000 == 0 or track["bestFit"]>track["lastFit"]:
            # This should really be put under a -v option
            print("Generation ",track["generationCount"],"Fitness ", track["bestFit"])
    return track["generationCount"] * population

class ThreadableGenefind:
    """An OOP version of the genefind mainloop which exposes its important tracking 
    values as attributes."""
    def run(self, target_string, fitness_percentile,
            population, initial_string_size, shared_state=None):
        if shared_state:
            shared_threads = shared_state[0]
            thread_id = shared_state[1]
            shared_threads[thread_id] = 0
            out_queue = shared_state[2]
            self.ready = shared_state[3]
            self.ready.acquire()
        gene_population = [initial(initial_string_size)]
        fitness = target_string
        fitness_cutoff = (100 - fitness_percentile) / 100
        self.population = population
        self.generation_count = 0
        self.current_fit = 0.0
        self.last_fit = 0.0
        self.best_fit = 0.0
        self._stopped = False
        while 1:
            # Update external performance metric
            if shared_threads[thread_id] is False:
                self._stopped = True
            else:
                shared_threads[thread_id] = self.performance()
            if self._stopped:
                break
            if self.best_fit == 100:
                break
            self.generation_count += 1
            gene_population = self.record(gene_population)
            gene_population = Mod2Run(gene_population, population)
            gene_population = Mod4Run(gene_population, fitness, fitness_cutoff)

            #if self.generation_count % 1000 == 0 or self.best_fit > self.last_fit:
                # This should really be put under a -v option
                #print("Generation ", self.generation_count, "Fitness ", self.best_fit)
        self._stopped = True
        try:
            out_queue.put(self.performance())
            self.ready.release()
        except NameError:
            return self.performance()

    def record(self, gene_population):
        """Do record keeping on the main loop of the algorithm. Update attributes
        and check to see if we've found the result we're looking for."""
        bestE = gene_population[0]
        if len(gene_population) == 1:
            return gene_population
        gene_population_out = [gene[1] for gene in gene_population]
        self.last_fit = self.current_fit
        self.current_fit = bestE[0]
        bestFit = self.best_fit
        if bestFit<bestE[0]:
            self.best_fit = bestE[0]
            if bestE[0] == 100:
                print("Result Found.","\n"\
                      ,"Generation count =", self.generation_count, '\n'\
                      ,"String :\n", bestE[1])
        return gene_population_out

    def performance(self):
        return self.generation_count * self.population

    def stopped(self):
        return self._stopped
    
    def stop(self):
        self._stopped = True

def fp_cull(parameter_population, fitness_percentile):
    """Cull the parameter population to find its top members above the 
    fitness percentile."""
    parameter_population.sort(key=(lambda candidate: candidate["performance"]))
    fitness_cutoff = -round(len(parameter_population) * fitness_percentile)
    if not fitness_cutoff: # Handle case where we round to zero
        fitness_cutoff = 1
    return [candidate for candidate in reversed(parameter_population[fitness_cutoff:])]
    
def fp_sample(target_string, parameter_population, sample_runs,
              performance_limit, num_threads):
    """Sample the parameter population in the find-parameters routine by running
    each candidate parameter set multiple times and taking the median performance
    as its score."""
    thread_count = sample_runs
    for candidate in parameter_population:
        sample_runs = thread_count
        trials = []
        trials_queue = multiprocessing.Queue()
        threads_host = {}
        manager = multiprocessing.Manager()
        threads_shared = manager.dict()
        race_controller = manager.BoundedSemaphore(value=num_threads)
        for run in range(sample_runs):
            sample = ThreadableGenefind()
            run = multiprocessing.Process(target=sample.run,
                                          args=(target_string,
                                                candidate["fitness_percentile"],
                                                candidate["population"],
                                                candidate["string_size"],
                                                (threads_shared,
                                                 sample_runs,
                                                 trials_queue,
                                                 race_controller)))
            run.start()
            threads_host[sample_runs] = run
        while sample_runs:
            time.sleep(0.1)
            try:
                trials.append(trials_queue.get(block=False))
                sample_runs -= 1
            except:
                None
            for thread in threads_shared.keys():
                if threads_shared[thread] > performance_limit:
                    #TODO: Make this not an ugly hack
                    threads_shared[thread] = False # Send message to stop the thread
        candidate["performance"] = statistics.median(trials)
        for thread in threads_host.values():
            thread.terminate()
    return parameter_population
        

def fp_mutate(parameter_population, population):
    """Increase the parameter population to its full size, then mutate it."""
    original_population = parameter_population.copy()
    if len(parameter_population) < population:
        for index in range(population - len(parameter_population)):
            parameter_population.append(random.choice(original_population).copy())
    for candidate in parameter_population:
        # Mutate fitness percentile
        sign = random.randrange(2)
        mutation = random.randint(1,9) * 0.1
        if sign:
            if candidate["fitness_percentile"] + mutation > 99.9:
                candidate["fitness_percentile"] -= mutation
            else:
                candidate["fitness_percentile"] += mutation
        else:
            if candidate["fitness_percentile"] - mutation < 0.1:
                candidate["fitness_percentile"] += mutation
            else:
                candidate["fitness_percentile"] -= mutation

        # Mutate population
        sign = random.randrange(2)
        mutation = random.randint(1,9)

        if sign:
            if candidate["population"] + mutation > 1000:
                candidate["population"] -= mutation
            else:
                candidate["population"] += mutation
        else:
            if candidate["population"] - mutation < 1:
                candidate["population"] += mutation
            else:
                candidate["population"] -= mutation

        # Mutate string_size
        sign = random.randrange(2)
        mutation = random.randint(1,9)

        if sign:
            if candidate["string_size"] + mutation > 1000:
                candidate["string_size"] -= mutation
            else:
                candidate["string_size"] += mutation
        else:
            if candidate["string_size"] - mutation < 1:
                candidate["string_size"] += mutation
            else:
                candidate["string_size"] -= mutation
        
    return parameter_population
            
            

def fp_record(tracking_dict, parameter_population):
    tracking_dict["last_best"] = tracking_dict["current_best"]
    tracking_dict["current_best"] = parameter_population[-1]
    if (tracking_dict["absolute_best"]["performance"] <
        tracking_dict["current_best"]["performance"]):
        tracking_dict["absolute_best"] = parameter_population[-1]
    tracking_dict["history"].append(parameter_population)
    return tracking_dict

def find_parameters(target_string, generations=10, sample_runs=5,
                    population=5, fitness_percentile=90, num_threads=1,
                    outpath=None):
    """Find the parameters that minimize the number of individuals for genefind.

    This is done using a genetics algorithm that starts with an initial parameter
    set, then mutates and finds the fitness of each member, finally culling the 
    members which do not meet a certain level of relative performance."""
    fitness_cutoff = (100 - fitness_percentile) / 100
    initial_parameters = {"fitness_percentile":90,
                          "population":100,
                          "string_size":50,
                          "performance":518600}
    parameter_population = [initial_parameters]
    tracking = {"generation_count":0,
                "absolute_best":initial_parameters,
                "current_best":initial_parameters,
                "last_best":initial_parameters,
                "history":[]}
    for generation in range(generations):
        tracking["generation_count"] += 1
        tracking = fp_record(tracking, parameter_population)
        print("Generation {}: Current best fit is ({},{},{}) with performance {}.".format(
            tracking["generation_count"],
            tracking["current_best"]["fitness_percentile"],
            tracking["current_best"]["population"],
            tracking["current_best"]["string_size"],
            tracking["current_best"]["performance"]))
        parameter_population = fp_mutate(parameter_population, population)
        performance_limit = tracking["current_best"]["performance"] * 200 # rough heuristic of when to quit
        parameter_population = fp_sample(target_string,
                                         parameter_population,
                                         sample_runs,
                                         performance_limit,
                                         num_threads)
        parameter_population = fp_cull(parameter_population, fitness_cutoff)
    if outpath:
        with open(outpath, 'w') as outfile:
            json.dump(tracking, outfile)
    else:
        pprint.pprint(tracking)
        
def main():
    """Run the mainloop and track fitness between generations."""
    parser = ArgumentParser()
    parser.add_argument("genetic_string")
    parser.add_argument("--meta", action="store_true", help="Enable the find-parameters meta-algorithm.")
    parser.add_argument("--meta-gen", type=int, default=10, dest="gens",
                        help="How many generations to run find-parameters for.")
    parser.add_argument("--meta-samples", type=int, default=5, dest="samples",
                        help="How many sample runs to do in find-parameters.")
    parser.add_argument("--meta-population", type=int, default=5, dest="mpop",
                        help="What population of parameters to use in find-parameters.")
    parser.add_argument("--meta-fitness", type=float, default=90, dest="mfp",
                        help="What fitness percentile from 1 to 99.999 to cull per generation of find-parameters.")
    parser.add_argument("--meta-threads", type=int, default=1, dest="threads",
                        help="How many threads to run find-parameters with.")
    parser.add_argument("--meta-output", type=str, default=None, dest="outpath",
                        help="Optional filepath to write history and results file to.")
    parser.add_argument("--fitness-percentile", type=float, default=90, dest="fp",
                        help=("Number from 1 to 99.999... specifying the " 
                              "fitness cutoff per generation."))
    parser.add_argument("--population", type=int, default=100, dest="pop",
                        help=("An integer number representing the population size to use."))
    parser.add_argument("--initial-ss", type=int, default=50, dest="string_size",
                        help="Integer representing initial strength length.")
    arguments = parser.parse_args()
    if arguments.meta:
        find_parameters(arguments.genetic_string,
                        generations=arguments.gens,
                        sample_runs=arguments.samples,
                        population=arguments.mpop,
                        fitness_percentile=arguments.mfp,
                        num_threads=arguments.threads,
                        outpath=arguments.outpath)
    else:                
        run_genefind(arguments.genetic_string,
                     arguments.fp,
                     arguments.pop,
                     arguments.string_size)
    
    
# Should really add an option to test performance
if __name__ == '__main__':
    main()
#cProfile.run('main()')
#find_parameters("ACGTAC",num_threads=4)
#test = ThreadableGenefind()
#test.run("ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT",
#         90,
#         100,
#         50)
    
    
    
