def analyze_log_data(file_path):
    action_counts = {}
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            for line in file:
                if 'INFO - User Action' in line:
                    action = line.split('Action: ')[1].split(',')[0].strip()
                    status = line.split('Status: ')[1].split(',')[0].strip()

                    if action not in action_counts:
                        action_counts[action] = {'Success': 0, 'Failed': 0}

                    if status == 'Success':
                        action_counts[action]['Success'] += 1
                    elif status == 'Failed':
                        action_counts[action]['Failed'] += 1

        return action_counts
    except Exception as e:
        return f"Error processing log file: {e}"

# Replace 'path_to_log_file.log' with the path to your log file
log_file_path = 'bot_log.log'
log_analysis_result = analyze_log_data(log_file_path)
print(log_analysis_result)
