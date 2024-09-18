"""
    Parse, analyse and create figures from the agent responses.
"""
import sys
from pathlib import Path
import argparse

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from glob import glob
import lib.visualize as visu
import lib.analyse as analyse
import lib.visualize as visu

def main(agent_responses_path: str, output_analysis_path: str):
    AGENT_RESPONSES_PATH = agent_responses_path
    OUTPUT_ANALYSIS_PATH = output_analysis_path
    PARSED_RESPONSES_PATH = f"{OUTPUT_ANALYSIS_PATH}/parsed_responses/"
    NETWORK_REPONSES_PATH = f"{OUTPUT_ANALYSIS_PATH}/network_responses/"
    RESULTS_PATH = f"{OUTPUT_ANALYSIS_PATH}/results/"

    GRAPH_NAMES = {
        'fully_connected' : 'Fully\nConnected',
        'fully_disconnected' : 'Fully\nDisconnected',
        'random' : 'Random',
        'scale_free' : 'Scale-Free'
    }

    GRAPH_COLORS = {
        'fully_connected': '#F7C088',
        'fully_disconnected': '#C1EDED',
        'random': '#C4A2DF',
        'scale_free': '#8BA7D4'
    }

    Path(PARSED_RESPONSES_PATH).mkdir(parents=True, exist_ok=True)
    Path(NETWORK_REPONSES_PATH).mkdir(parents=True, exist_ok=True)
    Path(RESULTS_PATH).mkdir(parents=True, exist_ok=True)

    response_dirs = [Path(str_path) for str_path in glob(f'{AGENT_RESPONSES_PATH}*', recursive=False)]
    for response_path in response_dirs:
        analyse.analyse_simu(agent_response=response_path,
                            analyse_dir=Path(OUTPUT_ANALYSIS_PATH),
                            graph_names=GRAPH_NAMES,
                            graph_colors=GRAPH_COLORS,
                            gifs = False)
    visu.accuracy_vs_network(f"{RESULTS_PATH}**/accuracy_per_network_and_repeat.csv",
                          RESULTS_PATH, GRAPH_NAMES, GRAPH_COLORS)

    visu.accuracy_vs_round(f"{RESULTS_PATH}**/accuracy_per_round.csv",
                           RESULTS_PATH, GRAPH_NAMES, GRAPH_COLORS)

    visu.correct_prop_vs_network(f"{RESULTS_PATH}**/consensus.csv",
                                 RESULTS_PATH, GRAPH_NAMES, GRAPH_COLORS)

    visu.consensus_table(f"{RESULTS_PATH}**/consensus.csv",
                           RESULTS_PATH)

    analyse.calculate_cost_per_round(f"{RESULTS_PATH}/cost_per_round.csv")

    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse, analyse and create figures from the agent responses.")
    parser.add_argument(
        "--compression_rate",
        type=float,
        required=True,
        help="The compression rate used in the experiment."
    )
    parser.add_argument(
        "--root_dir",
        type=str,
        default=".",
        help="Root directory of the project."
    )
    args = parser.parse_args()

    # フォーマットした圧縮率をディレクトリ名に使用（小数点を取り除く）
    formatted_rate = str(args.compression_rate).replace('.', '')
    agent_responses_path = f"{args.root_dir}/outputs/output_{formatted_rate}/agent_responses/"
    output_analysis_path = f"{args.root_dir}/outputs/output_{formatted_rate}/analysis/"

    main(agent_responses_path, output_analysis_path)
