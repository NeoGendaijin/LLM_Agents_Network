import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import os
import csv
import glob
import pandas as pd
from collections import Counter
from lib.agent import parse_response_mmlu
import networkx as nx
import matplotlib.pyplot as plt
import imageio
import seaborn as sns

GRAPH_TYPE = ['fully_connected_network']#,
                # 'fully_disconnected_network',
                # 'scale_free_network',
                # 'random_network',
                # 'watts_strogatz_network']

AGENT_RESPONSES_REP = 'output/agent_responses/'
OUTPUT_ANALYSE_REP = "output/analysis/"

class Analyse:
    """Meta data for a given graph and size"""

    def __init__(self, csv_path: str) -> None:
        # Type is a int, it is easier to compare
        self.type = file_name = GRAPH_TYPE.index(csv_path.split('/')[2])
        self.num_agents = int(csv_path.split('/')[3].split('.')[0])
        # The agent output is parsed and only the parsed file path is saved.
        self.path = parse_output_mmlu(csv_path, GRAPH_TYPE[self.type], self.num_agents)
        self.__accuracy = None
        self.__consensusPerQuestion = None
        self.__consensus = None
        self.__consensusSimpson = None

    def setAccuracy(self) -> None:
        self.__accuracy = calculate_accuracy(self.path)

    def setConsensusPerQuestion(self) -> None:
        self.__consensusPerQuestion = calculate_consensus_per_question(self.path)

    def setConsensus(self) -> None:
        self.__consensus = self.getConsensusPerQuestion()['consensus'].mean()

    def setConsensusSimpson(self) -> None:
        '''
            The probability that two different agents randomly selected heve the
        same responses.
        '''
        self.__consensusSimpson = self.getConsensusPerQuestion()['simpson'].mean()
        

    def getAccuracy(self) -> list[int]:
        # We check if it as already been computed
        if self.__accuracy is None:
            self.setAccuracy()
        return self.__accuracy

    def getConsensusPerQuestion(self) -> pd.DataFrame:
        # We check if it as already been computed
        if self.__consensusPerQuestion is None:
            self.setConsensusPerQuestion()
        return self.__consensusPerQuestion

    def getConsensus(self) -> float:
        # We check if it as already been computed
        if self.__consensus is None:
            self.setConsensus()
        return self.__consensus

    def getConsensusSimpson(self) -> float:
        # We check if it as already been computed
        if self.__consensusSimpson is None:
            self.setConsensusSimpson()
        return self.__consensusSimpson        

    def ParseOpinionEvolution(self) -> pd.DataFrame :
        return find_evolutions(self.path)

    def plotDynamicEvolution(self) -> None :
        created_figs(self.path)

def created_figs(parsed_file_path: str, network_type: str) -> None:

    df = pd.read_csv(parsed_file_path, delimiter='|')

    df['parsed_response'] = df['response'].apply(parse_response_mmlu)
    df['correct'] = df['parsed_response'] == df['correct_response']

    num_agents = df['agent_id'].unique().max() + 1

    graph = nx.read_graphml(f'experiment/data/{network_type}/{num_agents}.graphml')
    pos = nx.spring_layout(graph)

    rounds = df['round'].unique()
    questions = df['question_number'].unique()

    for question in questions:
        images = []  # To store paths of images for the current question
        for round_ in rounds:
            round_df = df[(df['round'] == round_) & (df['question_number'] == question)]
            color_map = ['green' if row['correct'] else 'red' for _, row in round_df.iterrows()]

            plt.figure(figsize=(10, 8))
            nx.draw(graph, pos=pos, node_color=color_map, with_labels=True, node_size=700)
            plt.title(f'Q{question} R{round_}')

            # Add round number text on the plot
            plt.text(0.05, 0.95, f'Round: {round_}', transform=plt.gca().transAxes, fontsize=14, verticalalignment='top', bbox=dict(boxstyle="round", alpha=0.5, facecolor='white'))

            # Save the plot for the current round
            image_path = f'output/figs/{network_type}/{num_agents}_q{question}_r{round_+1}.png'
            directory = os.path.dirname(image_path)

            # Ensure the directory exists
            os.makedirs(directory, exist_ok=True)
            plt.savefig(image_path)
            plt.close('all')

            images.append(image_path)

        # Create a GIF for the current question
        gif_path = f'output/figs/{network_type}/{num_agents}_q{question}.gif'
        with imageio.get_writer(gif_path, mode='I', fps=1, loop=0) as writer:
            for image_path in images:
                image = imageio.v3.imread(image_path)
                writer.append_data(image)
        
        # Optional: Remove the individual round images to clean up
        for image_path in images:
            os.remove(image_path)

# Function to calculate the accuracy of group responses for each round
def calculate_accuracy(parsed_file_path: str) -> pd.DataFrame:
    # Read the CSV file
    df = pd.read_csv(parsed_file_path, delimiter='|')

    num_agent = df['agent_id'].unique().size

    # We select only the correct responses and remove unecessary columns 
    accuracy_per_round = df[['round', 'question_number', 'correct']].query('correct')
    accuracy_per_round.to_csv(Path(f'{OUTPUT_ANALYSE_REP}step1.csv', index=False))

    # We count correct answers for each line
    accuracy_per_round = accuracy_per_round.groupby(['round', 'question_number']).count().reset_index()
    accuracy_per_round.to_csv(Path(f'{OUTPUT_ANALYSE_REP}step2.csv', index=False))

    # The network gives the right answer to a question if count > num agent / 2 
    accuracy_per_round['accuracy'] = accuracy_per_round['correct'].apply(lambda correct_num : 1 if correct_num > num_agent / 2 else 0)

    # Then we compute the average accuracy (for each round)
    accuracy_per_round = accuracy_per_round[['round', 'accuracy']].groupby('round').mean()

    accuracy_per_round.to_csv(Path(f'{OUTPUT_ANALYSE_REP}step3.csv', index=False))
    return accuracy_per_round

def find_evolutions(parsed_file_path) -> pd.DataFrame :
    opinion_evol_list = [] # list to be turned into a dataframe
    df = pd.read_csv(parsed_file_path, delimiter='|')

    for id in df['agent_id'].unique():
        for question in df['question_number'].unique():
            for round in [1,2]:
                prev = df.query(f'agent_id == {id} & question_number == {question} & round == {round-1}')
                assert len(prev.axes[0]) == 1
                next = df.query(f'agent_id == {id} & question_number == {question} & round == {round}')
                assert len(next.axes[0]) == 1

                # Here we determine wich type of evolution we have : 00, 01, 10 or 11,
                # with 0 wrong answer and 1 the good one (01 = from 1 to 0).
                type = None
                if bool(prev['correct'].values[0]):
                    type = "1"
                else :
                    type = "0"
                if bool(next['correct'].values[0]):
                    type = type+"1"
                else :
                    type = type+"0"
                opinion_evol_list.append([id, str(round), type])
    return pd.DataFrame(columns = ['agent_id', 'round', 'type'], data=opinion_evol_list)   

def calculate_consensus_per_question(parsed_file_path: str) -> pd.DataFrame :
    """
    """
    # Read the CSV file
    df = pd.read_csv(parsed_file_path, delimiter='|')

    num_agent = df['agent_id'].unique().size

    # We select only the correct responses in the last round and remove unecessary columns 
    final_consensus = df.query('correct & round == 2')[['question_number', 'correct']]

    # We count the proportion of agent with a correct answers for each question
    final_consensus = final_consensus.groupby(['question_number']).count().reset_index()
    final_consensus['consensus'] = final_consensus['correct'].apply(lambda correct : correct/num_agent)

    # Simpson consensus computation. This accuracy is computed as the probability that two answers
    # randomly selected are the same.
    simpson = df.query("round == 2").groupby(['question_number', 'parsed_response']).size().reset_index(name = 'count')
    simpson['simpson'] = simpson['count'].apply(lambda count : count/num_agent).apply(lambda p : p*p)
    simpson = simpson.groupby('question_number').sum().reset_index()[['question_number', 'parsed_response', 'simpson']]

    # Finally, we join tables
    final_consensus = pd.merge(final_consensus, simpson, on = 'question_number')#.set_index(to = 'question_number')
    return final_consensus[['question_number', 'parsed_response', 'consensus', 'simpson']]

def parse_output_mmlu(csv_file: str, res_file_name : str, num_agents: int) -> str:
    """
        Parse agent response to analyse which answer is correct and which is not.
    Save the result in OUTPUT_ANALYSE_REP, adding '_parsed' res_file_name.
    Return the path of the result file.
    """
    df = pd.read_csv(csv_file, delimiter='|')

    # analysing responses to find the correct ones
    df['parsed_response'] = df['response'].apply(parse_response_mmlu)
    df['correct'] = df['parsed_response'] == df['correct_response']

    # removing useless columns
    df = df[['agent_id', 'round', 'question_number', 'parsed_response','correct']]

    # saving data, creating the directory if it doesnot exist
    save_path = f'{OUTPUT_ANALYSE_REP}parsed_agent_responses/'
    Path(save_path).mkdir(parents=True, exist_ok=True)

    save_path = f'{save_path}{res_file_name}_{num_agents}_parsed.csv'
    df.to_csv(save_path, mode='w', sep='|', index=False)

    return save_path

if __name__ == "__main__":
    
    # Create the new directory structure if it does not exist
    Path(OUTPUT_ANALYSE_REP).mkdir(parents=True, exist_ok=True)

    # Specify the path to your CSV files
    csv_files = glob.glob(f'{AGENT_RESPONSES_REP}**/*.csv', recursive=True)

    # analyses[i] is a list wich contain analyses relative to graphs of type i
    analyses = [None] * len(GRAPH_TYPE)

    # reset result files and write headers
    f = open(f'{OUTPUT_ANALYSE_REP}accuracy.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(['graph_type', 'size', 'accuracy round 1', 'accuracy round 2', 'accuracy round 3'])
    f.close()

    f = open(f'{OUTPUT_ANALYSE_REP}consensus.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(['graph_type', 'size', 'consensus', 'consensus_simpson'])
    f.close()

    # Loop on each csv file
    for file in csv_files:
        print(file)
        current_analyse = Analyse(file) 
        
        # Create figs for each simulation
        # created_figs(file, GRAPH_TYPE[current_analyse.type])

        # Calculate the accuracy of group responses
        accuracy = current_analyse.getAccuracy()

        # save accuracy
        with open(f'{OUTPUT_ANALYSE_REP}accuracy.csv', 'a', newline='') as result_file:
            writer = csv.writer(result_file)
            writer.writerow([GRAPH_TYPE[current_analyse.type],
                             current_analyse.num_agents,
                             accuracy.query('round == 0').values[0][0],
                             accuracy.query('round == 1').values[0][0],
                             accuracy.query('round == 2').values[0][0]])
            
        # Calculate the consensus for this graph
        consensus = current_analyse.getConsensusPerQuestion()

        # create the result path or reset if it already exists
        result_file_path = f'{OUTPUT_ANALYSE_REP}consensus/{GRAPH_TYPE[current_analyse.type]}/'
        Path(result_file_path).mkdir(parents=True, exist_ok=True)

        # Draw plots and save them
        plt.figure(figsize=(16, 9))
        sns.displot(consensus, x="consensus")
        plt.title(f"average consensus per question for {current_analyse.num_agents} agents\nin {GRAPH_TYPE[current_analyse.type]}")
        plt.xlabel("consensus (proportion of correct answers)")
        plt.ylabel("frequency (%)")
        plt.savefig(f'{result_file_path}consensus_{current_analyse.num_agents}.png')
        plt.close('all')

        plt.figure(figsize=(16, 9))
        sns.displot(consensus, x="simpson")
        plt.title(f"average simpson consensus per question for {current_analyse.num_agents} agents\nin {GRAPH_TYPE[current_analyse.type]}")
        plt.xlabel("simpson probability")
        plt.ylabel("frequency (%)")
        plt.savefig(f'{result_file_path}simpson_{current_analyse.num_agents}.png')
        plt.close('all')

        # save the csv file
        consensus.to_csv(f'{result_file_path}{current_analyse.num_agents}.csv', mode='w', sep=',', index=False)

        # save the mean for both metrics
        with open(f'{OUTPUT_ANALYSE_REP}consensus.csv', 'a', newline='') as result_file:
            writer = csv.writer(result_file)
            writer.writerow([GRAPH_TYPE[current_analyse.type],
                             current_analyse.num_agents,
                             current_analyse.getConsensus(),
                             current_analyse.getConsensusSimpson()])

        # # Parse the opinion evolution list and display it
        # opinion_evol = current_analyse.ParseOpinionEvolution()
        # plt.figure()
        # sns.histplot(data=opinion_evol, x="round", hue="type", multiple="dodge", shrink=.8, stat="count")
        # plt.grid()
        # plt.xlabel("round number")
        # plt.ylabel("number of agents")
        # plt.title(f"opinion changes during the round for {current_analyse.num_agents} agents \nin a {GRAPH_TYPE[current_analyse.type]}")

        # # Save the fig
        # file_path = f'{OUTPUT_ANALYSE_REP}/opinion_changes/{GRAPH_TYPE[current_analyse.type]}/'
        # Path(file_path).mkdir(parents=True, exist_ok=True)
        # plt.savefig(Path(f'{file_path}/{current_analyse.num_agents}.png'))
        # plt.close('all')

        # add analyse to the list for later
        if not (analyses[current_analyse.type]):
            analyses[current_analyse.type] = []
        analyses[current_analyse.type].append(current_analyse)

    # accuracy comparison plot
    # number of agent vs accuracy
    plt.figure(figsize=(16, 9))
    for graph_type in range(len(analyses)):
        curve = []
        for analyse in analyses[graph_type]:
            curve.append( (analyse.num_agents, analyse.getAccuracy().query('round == 2').values[0][0]) )
        curve.sort(key = lambda point: point[0])
        X = [point[0] for point in curve]
        Y = [point[1] for point in curve]
        plt.plot(X, Y, label=GRAPH_TYPE[graph_type])
    plt.title("accuracy vs graph size and graph type")
    plt.legend()
    plt.xlabel('Number of agents')
    plt.ylabel('accuracy (%)')
    plt.grid(True)
    plot_path = Path(OUTPUT_ANALYSE_REP + 'accuracy_vs_number_of_agents.png')
    plt.savefig(plot_path)
    plt.close('all')

    # round vs accuracy
    plt.figure(figsize=(16, 9))
    for graph_type in range(len(analyses)):
        for analyse in analyses[graph_type]:
            Y = analyse.getAccuracy()
            plt.plot(['1', '2', '3'], Y, label=f'{GRAPH_TYPE[graph_type]}_{analyse.num_agents}')
    plt.title("accuracy vs round number and graph type")
    plt.legend()
    plt.xlabel('Round number')
    plt.ylabel('accuracy (%)')
    plt.grid(True)
    plot_path = Path(OUTPUT_ANALYSE_REP + 'accuracy_vs_round.png')
    plt.savefig(plot_path)
    plt.close('all')

    # consensus vs graph type
    plt.figure(figsize=(16, 9))
    for graph_type in range(len(analyses)):
        curve = []
        for analyse in analyses[graph_type]:
            curve.append([analyse.num_agents, analyse.getConsensus()])
        curve.sort(key = lambda point: point[0])
        X = [point[0] for point in curve]
        Y = [point[1] for point in curve]
        plt.plot(X, Y, label = GRAPH_TYPE[graph_type])
    plt.title("consensus vs agent graph size and graph type")
    plt.legend()
    plt.xlabel('number of agents (graph size)')
    plt.ylabel('consensus (%)')
    plt.grid(True)
    plot_path = Path(OUTPUT_ANALYSE_REP + 'consensus_vs_network.png')
    plt.savefig(plot_path)
    plt.close('all')

    # simpson consensus vs graph type
    plt.figure(figsize=(16, 9))
    for graph_type in range(len(analyses)):
        curve = []
        for analyse in analyses[graph_type]:
            curve.append([analyse.num_agents, analyse.getConsensusSimpson()])
        curve.sort(key = lambda point: point[0])
        X = [point[0] for point in curve]
        Y = [point[1] for point in curve]
        plt.plot(X, Y, label = GRAPH_TYPE[graph_type])
    plt.title("simpson consensus vs agent graph size and graph type")
    plt.legend()
    plt.xlabel('number of agents (graph size)')
    plt.ylabel('consensus (%)')
    plt.grid(True)
    plot_path = Path(OUTPUT_ANALYSE_REP + 'simpson_consensus_vs_network.png')
    plt.savefig(plot_path)
    plt.close('all')