#Impact of Communication Masking on Problem Solving in LLM Agent Networks

This repository contains the code and experiments for the paper:

**"Impact of Communication Masking on Problem Solving in LLM Agent Networks"**

In this study, we simulate a network of Large Language Model (LLM) agents communicating using natural language. By introducing communication masking—selectively masking words during agent interactions—we investigate how information bottlenecks affect collective problem-solving abilities across different network topologies.

Our findings highlight the critical role of network structure in maintaining effective collaboration under communication constraints. Certain network configurations demonstrate robustness to masking, while others experience significant performance degradation. These insights have implications for designing resilient distributed systems and artificial intelligence applications where information flow may be limited or disrupted.

## Introduction

The advent of Large Language Models (LLMs) has revolutionized artificial intelligence by enabling machines to understand and generate human-like language with remarkable proficiency. Integrating LLMs into multi-agent systems allows for complex interactions where agents communicate to achieve collective goals.

However, communication constraints—such as network limitations or deliberate information masking—can significantly impact the efficiency of these systems. This repository provides the code to simulate LLM agent networks under varying levels of communication masking and network topologies, allowing for the exploration of how information bottlenecks influence collective intelligence.

For a detailed explanation of the methodology and findings, please refer to the accompanying paper.

## Prerequisites

- **Python 3.8** or higher
- An **OpenAI API key** for accessing GPT-3.5-Turbo or GPT-4 models
- A **Hugging Face token** for downloading the MMLU dataset

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/NeoGendaijin/LLM_Agents_Network.git
   cd LLM_Agents_Network
   ```

2. **Set up environment variables**

   Create a `.env` file in the root directory and add your OpenAI API key and Hugging Face token:

   ```env
   OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
   HF_TOKEN=<YOUR_HUGGING_FACE_TOKEN>
   ```

3. **Install required packages**

   If you prefer using `pip`, you can install the packages directly:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Experiments

Navigate to the `experiment` directory and run the `run.sh` script:

```bash
cd experiment
./runmain.sh
```

```bash
cd experiment
./runanalysis.sh
```

This script executes the experiment pipeline, which includes:

1. **Generating Networks**: Creates the network topologies used in the simulations (`generate_networks.py`).
2. **Simulating Agent Interactions**: Runs the multi-agent simulations with communication masking (`main.py`).
3. **Analyzing Results**: Processes the simulation data and generates figures (`analysis.py`).

### Notes

- Ensure that your OpenAI API usage complies with their terms and conditions.
- The simulations may take some time to run, depending on the number of agents and debate rounds configured.

## Configuring Experiments

You can customize the experiments by adjusting parameters in the configuration files or directly in the scripts:

- **Masking Rates**: Set the percentage of words to mask during agent communication.
- **Network Topologies**: Choose between fully connected, fully disconnected, random, and scale-free networks.
- **Number of Agents**: Modify the number of agents participating in the simulations.
- **Debate Rounds**: Change the number of communication rounds between agents.
