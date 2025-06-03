import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Plot closing ranks over years.')
parser.add_argument('--college_type', type=str, choices=['NIT', 'IIIT', 'GFTI'], help='College type (NIT, IIIT, GFTI)')
parser.add_argument('--branch_number', type=int, help='Branch number')
parser.add_argument('--rank_number', type=int, help='Rank number to center the plot around')
parser.add_argument('--list_branches', action='store_true', help='List available branches and exit')
args = parser.parse_args()

df = pd.read_csv('historical_data.csv')

# List available branches and exit
if args.list_branches:
    available_branches = df['academic_program_name'].unique()
    print("Available Branches:")
    for i, branch in enumerate(available_branches):
        print(f"{i+1}: {branch}")
    exit()

# Check if required arguments are provided
if not all([args.college_type, args.branch_number, args.rank_number]):
    parser.error("The following arguments are required: --college_type, --branch_number, --rank_number")

plt.figure(figsize=(20, 30))

# Get branch name from branch number
branch_number = args.branch_number
available_branches = df['academic_program_name'].unique()
if branch_number < 1 or branch_number > len(available_branches):
    print("Invalid branch number.")
    exit()
branch = available_branches[branch_number - 1]

# Filter by college type
college_type = args.college_type
if college_type == "NIT":
    college_filter = "national institute of technology"
elif college_type == "IIIT":
    college_filter = "indian institute of information technology"
else:
    college_filter = ""

if college_type == "GFTI":
    program_df = df[(df['academic_program_name'] == branch) & (df['is_final_round'] == 1) & (~df['college_name'].str.lower().str.contains("national institute of technology")) & (~df['college_name'].str.lower().str.contains("indian institute of information technology"))]
else:
    program_df = df[(df['academic_program_name'] == branch) & (df['is_final_round'] == 1) & (df['college_name'].str.lower().str.contains(college_filter))]

if program_df.empty:
    print(f"No data found for {college_type} in branch {branch}.")

# Group by college and academic program
grouped = program_df.groupby(['college_name', 'academic_program_name'])

# Use a colormap to generate distinct colors for each group
cmap = cm.get_cmap('tab20', len(grouped))

# Plot the closing ranks for each group
for i, (name, group) in enumerate(grouped):
    color = cmap(i)
    college_name = group['college_name'].iloc[0]
    place_name = college_name
    plt.plot(group['year'], group['closing_rank'], marker='o', color=color)
    ha = 'left' if i % 2 == 0 else 'right'
    xytext_x = 10 if i % 2 == 0 else -10
    truncated_college_name = place_name
    # Find the year where closing_rank is closest to rank_number
    closest_year_index = (group['closing_rank'] - args.rank_number).abs().idxmin()
    closest_year = group.loc[closest_year_index, 'year']
    closest_rank = group.loc[closest_year_index, 'closing_rank']

    plt.annotate(truncated_college_name, xy=(closest_year, closest_rank), textcoords="offset points", xytext=(xytext_x,10), ha=ha)
    plt.text(group['year'].iloc[-1] + 0.1, group['closing_rank'].iloc[-1], str(group['closing_rank'].iloc[-1]), ha='left', va='center')

title = f"{college_type}: {branch}"
plt.title(title)
plt.xlabel('Year')
plt.ylabel('Closing Rank')
plt.gca().yaxis.set_ticks_position('right')
plt.gca().yaxis.set_label_position('right')

plt.gca().set_xticks(program_df['year'].unique())
plt.grid(True)
plt.tight_layout(rect=[0, 0.05, 1, 0.95])

# Adjust y-axis limits
rank_number = args.rank_number
min_rank = program_df['closing_rank'].min()
plt.ylim(min_rank - 5000, rank_number + 15000)

# Save the plot as a PNG image
filename = f"{college_type.lower()}_branch{branch_number}.png"
plt.savefig(filename)
plt.close()
