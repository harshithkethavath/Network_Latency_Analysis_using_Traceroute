import argparse, subprocess, os, time, shutil, re, json, random
from statistics import mean, median
import matplotlib.pyplot as plot
results_folder = 'results'


def traceroute(destination, max_hops, run_number):
    traceroute_out = subprocess.check_output(['traceroute', destination, '-m', str(max_hops)]).decode('utf-8')
    lines = traceroute_out.strip().splitlines()

    if not os.path.exists(results_folder):
        os.mkdir(results_folder)
    
    results_file = "result-run" + str(run_number) + ".out"
    results_path = os.path.join(results_folder, results_file)

    with open(results_path, "w") as file:
        for line in lines:
            file.write(str(line) + "\n")


def results_extractor(results_location):
    if os.path.exists(results_location):
        result_files = os.listdir(results_location)
        hop_hosts = {}
        hop_times = {}

        for file in result_files:
            file_path = os.path.join(results_location, file)

            if os.path.isfile(file_path):
                with open(file_path, "r") as result_file:
                    file_content = result_file.read().strip().splitlines()

                    for line in file_content[1:]:
                        items = line.split()
                        hop_number = int(items[0])

                        host = re.findall(r'(\S+) \((.*?)\)',line)
                        rtt = re.findall(r"(\d+\.\d+) ms",line)
                        multiple_hosts = []

                        if hop_number in hop_hosts:
                            hop_hosts[hop_number].append(multiple_hosts)
                        else:
                            hop_hosts[hop_number] = host

                        if hop_number in hop_times:
                            hop_times[hop_number].extend(rtt)
                        else:
                            hop_times[hop_number] = rtt

        hop_rtt = {}
        for times in hop_times:
            intermediate_list = []

            for time in hop_times[times]:
                no_unit = time[:-3]
                intermediate_list.append(float(no_unit))
            
            hop_rtt[times] = intermediate_list

        return(hop_hosts, hop_rtt)

    else:
        print("The folder does not exist.")


def unique_items(input_list):
    unique_list = []

    for item in input_list:
        if item not in unique_list:
            if item:
                unique_list.append(item)
    
    return unique_list


def json_generator(hop_hosts, hop_rtt, json_output_path):
    traceroute_data = []

    for (hop1, host), (hop2, rtt) in zip(hop_hosts.items(), hop_rtt.items()):
        data = {
            'avg': round(mean(rtt),3),
            'hop': hop1,
            'host': unique_items(host),
            'max': round(max(rtt),3),
            'med': round(median(rtt),3),
            'min': round(min(rtt),3)
        }
        traceroute_data.append(data)

    json_file_name = " "

    if json_output_path == " ":
        json_file_name = "data.json"
    
    elif os.path.exists(json_output_path):
        json_file_name = json_output_path + "/data.json"

    else:
        print("Given path does not exist JSON file is saved in current working directory.")
        json_file_name = "data.json"

    json_data = json.dumps(traceroute_data, indent = 4)
    with open(json_file_name, "w") as json_file:
        json_file.write(json_data)

    print("The JSON file is successfully created.")


def graph_generator(hop_rtt, graph_output_path):
    hop_numbers = sorted(hop_rtt.keys())
    rtt_values = [hop_rtt[hop] for hop in hop_numbers]

    plot.figure(figsize = (10, 6))
    plot.boxplot(rtt_values, patch_artist = True, showmeans = True)

    plot.xlabel("Hop Number")
    plot.ylabel("Latency (ms)")
    plot.title("Latency Distribution per Hop")

    plot.xticks(
        range(1, len(hop_numbers) + 1),
        labels = [
            f'Hop {hop}' 
            for hop
            in hop_numbers
        ],
        rotation = 45
    )

    if graph_output_path == " ":
        graph_file_path = 'output.pdf'

    elif os.path.exists(graph_output_path):
        graph_file_path = graph_output_path + '/output.pdf'

    else:
        graph_file_path = 'output.pdf'
        print("The given location is not valid and the file is saved in current working directory")

    plot.tight_layout()
    plot.savefig(graph_file_path)
    plot.close()

    print("The GRAPH file is successfully created.")


def output(result_location, json_location, graph_location):
    hop_hosts, hop_rtt = results_extractor(result_location)

    hosts = {
        hop:host
        for hop, host in hop_hosts.items()
        if host != []
    }

    rtt = {
        hop:rtts
        for hop, rtts in hop_rtt.items()
        if rtts != []
    }

    json_generator(hosts, rtt, json_location)
    graph_generator(rtt, graph_location)


def trstats():
    parser = argparse.ArgumentParser(description = "A script that performs statistical analysis on results from traceroute of a destination host or IP address")
    
    parser.add_argument('-n', dest = "NUM_RUNS", type = str, default = 5, help = "Number of times traceroute will run")
    parser.add_argument('-d', dest = "RUN_DELAY", type = int, default = 2, help = "Number of seconds to wait between two consecutive runs")
    parser.add_argument('-m', dest = "MAX_HOPS", type = int, default = 30, help = "Number of maximum hops per traceroute run")
    parser.add_argument('-o', dest = "OUTPUT", type = str, default = " ", help = "Path of output JSON file containing the statistics")
    parser.add_argument('-g', dest = "GRAPH", type = str, default = " ", help = "Path of the output PDF file containing statistical graph")
    parser.add_argument('-t', dest = "TARGET", type = str, help = "A target domain name or IP address (required if -test is absent)")
    parser.add_argument('--test', dest = "TEST_DIR", type = str, help = "Directory containing NUM_RUNS number of files, each of which contains the putput of a traceroute run. If present, this will override all other options and traceroute will not be invoked. Statistics will be computed over the traceroute output stored in the text files")

    args = parser.parse_args()

    if args.TEST_DIR:
        output(args.TEST_DIR, args.OUTPUT, args.GRAPH)

    elif args.TARGET:
        if os.path.exists(results_folder):
            shutil.rmtree(results_folder)

        for i in range(int(args.NUM_RUNS)):
            traceroute(args.TARGET, args.MAX_HOPS, i + 1)
            time.sleep(args.RUN_DELAY)

        output(results_folder, args.OUTPUT, args.GRAPH)
        
    
    else:
        print("Please mention the target host domain name or IP address")
        exit

    if args.OUTPUT == " ":
        print("The path of the output file is ./data.json")

    if args.GRAPH == " ":
        print("The path of the graph file is ./output.pdf")


if __name__ == "__main__":
    trstats()