"""
    Contains programms to analyse pandas dataframes.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple
import lib.parse as parse
import lib.visualize as visu
import networkx as nx
import glob
import os
import csv

pd.options.mode.chained_assignment = None

def analyse_simu(agent_response: Path,
                analyse_dir: Path,
                graph_names,
                graph_colors,
                gifs = False) -> Tuple[str, int, str]:
    '''
        Analyse the respones of agents from a single simulation run.

        Args:
            agent_response: Path to the agent response CSV file.
            analyse_dir: Path to the directory where the analysis results will be saved.
            gifs: Boolean to determine if the figures should be created or not.

        Returns:
            graph_type: The type of graph used in the simulation.
            num_agents: The number of agents in the simulation.
            network_bias: The type of network bias used in the simulation.
    '''

    # Parse the file name
    num_agents, graph_type = parse_file_path(agent_response)

    # Create the final result directories
    analyse_dir.mkdir(parents=True, exist_ok=True)

    # Parse the agent response
    agent_parsed_resp = parse.parse_output_mmlu(agent_response, analyse_dir / f'parsed_responses/{agent_response.name}.csv')
    network_responses_df = parse.get_network_responses(agent_parsed_resp, analyse_dir / f'network_responses/{agent_response.name}.csv')

    # Analyse the responses of this configuration
    results_path = analyse_dir / f'results/{agent_response.name}/'
    Path(results_path).mkdir(exist_ok=True)

    # Accuracy
    visu.accuracy_repartition(network_responses_df, f'{graph_type}', num_agents, results_path)

    # Consensus
    consensus_df = calculate_consensus_per_question(agent_parsed_resp, network_responses_df)
    visu.consensus_repartition(consensus_df, results_path, graph_colors, graph_names)

    # Opinion changes
    opinion_changes = find_evolutions(agent_parsed_resp)
    visu.opinion_changes(opinion_changes, f"{graph_type}", results_path, graph_names, graph_colors)

    # Neighbors
    calculate_proportion_neighbours_correct(agent_parsed_resp, graph_type, results_path)

    # Gifs
    if gifs:
        graphml_path = Path(f'experiment/data/{graph_type}/{num_agents}.graphml')
        visu.created_gifs(agent_parsed_resp, graphml_path, results_path / f'{agent_response.name}/gifs/')

    return graph_type, num_agents

def parse_file_path(dir_path : Path) -> Tuple[int, str, str]:
    '''
        Parse the file_path to determine the number of agents, the network bias the network type.

        Args:
            dir_path: Path to the agent response directory.

        Returns:
            number of agent: The number of agent in the simulation.
            graph_type: The type of graph used in the simulation.
    '''
    num_agents = 25 # fixed for this paper

    if "scale_free" in dir_path.name:
        graph_type = "scale_free"
    else:
        graph_type = dir_path.name

    return num_agents, graph_type

def rename_evolution(prev_correct, next_correct):
    """
        Return the type of evolution between two responses.

        Args:
            prev_correct: Boolean indicating if the previous response is correct.
            next_correct: Boolean indicating if the next response is correct.

        Returns:
            type: The type of evolution between the two responses.
    """
    type = None
    if bool(prev_correct):
        type = "C -> "
    else :
        type = "I -> "
    if bool(next_correct):
        type = type+"C"
    else :
        type = type+"I"
    return type

def find_evolutions(parsed_agent_response : pd.DataFrame) -> pd.DataFrame :
    """
    Return the list of changes that have occured in the simulation. For example, an agent changing is response from incorrect to correct.

    Args:
        parsed_agent_response: The parsed agent response dataframe.

    Returns:
        final_changes: The list of changes that have occured in the simulation.
    """
    df = parsed_agent_response.query("bias == 'unbiased'")
    final_changes : pd.DataFrame = None # Result

    # First we create a dataframe per round
    rounds: list[pd.DataFrame] = []
    for round in df['round'].unique():
        rounds.append(df.query(f'round == {round}'))

    # Then we join round n-1 and round n to record all changes
    for round in range(0,len(rounds)):
        prev, next = rounds[round-1], rounds[round]
        prev = prev.rename(columns={'correct' : 'prev_res', 'round': 'prev_round'})
        next = next.rename(columns={'correct' : 'cur_res'})
        changes = prev.merge(next, on=['network_number',
                                       'question_number',
                                       'repeat',
                                       'agent_id'])

        # We transform boolean into a string, "C" (correct) and "I" (Incorrect)
        changes['prev_res'] = changes['prev_res'].apply(lambda x : 'C' if x==True else 'I')
        changes['cur_res'] = changes['cur_res'].apply(lambda x : 'C' if x==True else 'I')

        changes['evolution'] = changes['prev_res'] + ' -> ' + changes['cur_res']
        changes = changes[['network_number',
                           'agent_id',
                           'round',
                           'question_number',
                           'repeat',
                           'evolution']]

        # concatenation of all rounds results
        if final_changes is None:
            final_changes = changes
        else :
            final_changes = pd.concat([final_changes, changes], axis=0)

    return final_changes

def calculate_proportion_neighbours_correct(parsed_agent_response: pd.DataFrame, graph_type: str, final_res_path: Path) -> pd.DataFrame:
    """
    Calculate the proportion of neighbors that were correct in the previous round for each agent in unbiased responses,
    separately for each round, question number, and repeat, and merge this data back into the original DataFrame.

    Args:
        parsed_agent_response (pd.DataFrame): DataFrame containing agents' responses and metadata.
        graph_type (str): The type of graph to load (defines the directory of GraphML files).
        final_res_path (Path): The path to save the final results.

    Returns:
        pd.DataFrame: The original DataFrame with an added column for the proportion of correct neighbors from the previous round.
    """
    df_final = pd.DataFrame(columns = ["network_number", "round", "question_number", "repeat",
                                        "agent_id", "correct_prev_round", "correct_this_round",
                                        "prop_correct_neighbors"])
    if graph_type == "fully_disconnected":
        df_final.to_csv(Path(final_res_path) / 'proportion_neighbors_correct_previous_round.csv', index=False)
        return df_final

    df = parsed_agent_response.copy().drop(['parsed_response','correct_response'], axis=1)
    for network_num in df['network_number'].unique():
        # We load the graph and build a pandas table containing all the edges
        graphml_path = Path(f'input/{graph_type}/{network_num}.graphml')
        G = nx.read_graphml(graphml_path)

        network_df = df.query(f"network_number == {network_num}")
        edge_list = []
        for edge in G.edges:
            edge_list.append([int(edge[0]), int(edge[1])])
            edge_list.append([int(edge[1]), int(edge[0])])
        df_edges = pd.DataFrame(columns = ["agent_id", "neihgbour_id"], data = edge_list).drop_duplicates()

        # Iterate over each unique combination of network number, question number, and repeat
        for round in network_df['round'].unique():
            if round == 0: # First round is skipped because it does not have a previous round
                continue
            # Cartesian product of each agent with all its neighbors for the given round
            partial_res_df = network_df.query(f"round == {round} & bias == 'unbiased'").merge(df_edges, on="agent_id")

            # We select the previous round responses and merge them with the cartesian product dataframe to have each
            # node's neihgbor response
            neihgbours_responses = network_df.query(f"round == {round-1}").rename(columns={"agent_id": "neihgbour_id",
                                                                                           "correct": "correct_neihbour"})
            partial_res_df = partial_res_df.merge(neihgbours_responses,
                                                  on = ["neihgbour_id", "question_number", "repeat"])

            # We aggregate the result by doing the mean over all the neihbours responses
            partial_res_df = partial_res_df.groupby(["agent_id",
                                                    "question_number",
                                                    "repeat",
                                                    "correct"]).agg(prop_correct_neighbors=("correct_neihbour", "mean")).reset_index()

            # Add missing data
            partial_res_df = partial_res_df.rename(columns={"correct": "correct_this_round"})
            partial_res_df['network_number'] = network_num
            partial_res_df['round'] = round

            # We use merge to add 1 last boolean columns: correct_previous_round
            previous_round = network_df.query(f"round == {round-1}")[["agent_id", "question_number",
                                                                    "repeat", "correct"]]
            previous_round = previous_round.rename(columns={"correct": "correct_prev_round"})
            partial_res_df = partial_res_df.merge(previous_round, on=["agent_id", "question_number","repeat"])

            # Concatenation to final result
            if df_final.empty:
                df_final = partial_res_df
            else:
                df_final = pd.concat([df_final, partial_res_df])

    df_final.to_csv(Path(final_res_path) / 'proportion_neighbors_correct_previous_round.csv', index=False)

    return df_final

def calculate_average_tokens(input_dir: str, output_dir: str):
    # すべてのCSVファイルを取得
    csv_files = glob.glob(f"{input_dir}/**/*.csv", recursive=True)

    all_data = []
    for file in csv_files:
        df = pd.read_csv(file, sep='|')
        all_data.append(df)

    # 全データを結合
    combined_df = pd.concat(all_data, ignore_index=True)

    # 各試行（network_type, network_num, repeat_num, question_number）ごとに平均を計算
    # 必要に応じてグループ化のキーを調整してください
    average_tokens = combined_df.groupby(['agent_id'])['input_tokens'].mean()

    # 必要に応じて結果を保存
    average_tokens.to_csv(f"{output_dir}/average_tokens.csv", sep='|')


def calculate_average_message_count(graphml_folder):
    message_counts = []

    # Loop through all files in the given folder
    for filename in os.listdir(graphml_folder):
        if filename.endswith('.graphml'):
            # Load the graph from the file
            graph = nx.read_graphml(os.path.join(graphml_folder, filename))
            # Get the number of edges in the graph
            message_count = graph.number_of_edges()
            message_counts.append((message_count * 2) + 25)

    # Calculate the average number of edges
    if message_counts:
        average_messages = sum(message_counts) / len(message_counts)
    else:
        average_messages = 0

    return average_messages

def calculate_cost_per_round(output_csv='output_cost.csv', results_path='./'):
    '''
    Calculate the average number of inputs and tokens per round for each network type.

    Args:
        output_csv: The path to the output CSV file.
        average_tokens_csv: The path to the average tokens CSV file.

    Returns:
        None
    '''

    network_types = ['fully_connected', 'fully_disconnected', 'random', 'scale_free']
    results = []

    # Load the average tokens per agent from CSV
    average_tokens_csv= results_path + 'average_tokens.csv'
    if not os.path.exists(average_tokens_csv):
        print(f"Average tokens CSV not found: {average_tokens_csv}")
        return

    avg_tokens_df = pd.read_csv(average_tokens_csv, sep='|')

    # Compute the overall average tokens across all agents
    overall_avg_tokens = avg_tokens_df['input_tokens'].mean()
    print(f"Overall Average Tokens per message: {overall_avg_tokens}")

    for network_type in network_types:
        graph_folder = f'input/{network_type}'
        graph_files = list(Path(graph_folder).glob('*.graphml'))

        if not graph_files:
            print(f"No GraphML files found for network type: {network_type}")
            continue

        average_messages = calculate_average_message_count(graph_folder)

        # Calculate average tokens per message
        # Assuming that each message corresponds to one input token count
        average_tokens_per_message = overall_avg_tokens

        # Calculate total tokens per round
        total_tokens_per_round = average_messages * average_tokens_per_message

        results.append((network_type, average_messages, total_tokens_per_round))

    # Write the results to a CSV file
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['network', 'inputs_per_round', 'tokens_per_round'])
        writer.writerows(results)

    print(f"Cost per round calculated and saved to {output_csv}")

def calculate_consensus_per_question(parsed_agent_response: pd.DataFrame, network_responses_df: pd.DataFrame):
    '''
    Returns consensus measure and Simpson consensus for each question in the parsed_agent_response DataFrame
    for questions which the system answered correctly and incorrectly.

    Args:
        parsed_agent_response: The parsed agent response dataframe.
        network_responses_df: The dataframe containing the system's response information.

    Returns:
        correct_consensus: The consensus measure and Simpson consensus for each question answered correctly.
        incorrect_consensus: The consensus measure and Simpson consensus for each question answered incorrectly.
    '''
    # Filter unbiased responses
    df = parsed_agent_response.query("bias == 'unbiased'")

    last_round = network_responses_df['round'].max()

    # Filter network_responses_df to include only correctly and incorrectly answered questions
    correct_questions = network_responses_df.query(f"round == {last_round} & correct == True")[['network_number', 'question_number', 'repeat']]
    incorrect_questions = network_responses_df.query(f"round == {last_round} & correct == False")[['network_number', 'question_number', 'repeat']]

    # Merge with the filtered parsed_agent_response to keep only the correct and incorrect questions
    correct_df = df.merge(correct_questions, on=['network_number', 'question_number', 'repeat'], how='inner')
    incorrect_df = df.merge(incorrect_questions, on=['network_number', 'question_number', 'repeat'], how='inner')

    # Function to compute consensus
    def compute_consensus(dataframe):
        # Calculate correct proportion for each question
        correct_prop = dataframe.groupby(['network_number', 'question_number', 'repeat'])['correct'].mean().reset_index()
        correct_prop = correct_prop.rename(columns={'correct': 'correct_prop'})

        # Calculate Simpson index
        counts = dataframe.groupby(['network_number', 'question_number', 'repeat', 'parsed_response']).size().reset_index(name='count')
        total_counts = counts.groupby(['network_number', 'question_number', 'repeat'])['count'].sum().reset_index(name='total')
        counts = counts.merge(total_counts, on=['network_number', 'question_number', 'repeat'])
        counts['proportion'] = counts['count'] / counts['total']
        counts['simpson'] = counts['proportion'] ** 2

        simpson = counts.groupby(['network_number', 'question_number', 'repeat'])['simpson'].sum().reset_index()

        final_consensus = pd.merge(correct_prop, simpson, on=['network_number', 'question_number', 'repeat'])

        return final_consensus

    # Compute consensus for correct and incorrect questions
    correct_consensus = compute_consensus(correct_df)
    incorrect_consensus = compute_consensus(incorrect_df)

    correct_consensus['network_correct'] = "true"
    incorrect_consensus['network_correct'] = "false"

    return pd.concat([correct_consensus, incorrect_consensus])


