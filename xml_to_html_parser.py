#!/usr/bin/env python3
"""
Pomodoro Leaderboard XML to HTML Parser
Converts Excel XML format leaderboard data to a beautiful HTML page
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class PomodoroLeaderboardParser:
    def __init__(self, xml_file: str):
        self.xml_file = xml_file
        self.dates = []
        self.users_data = {}
        self.mvp_data = {}
        self.totals = {}
        
    def parse_xml(self) -> bool:
        """Parse the Excel XML file and extract leaderboard data"""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            # Define namespace
            ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
            
            # Find the worksheet and table
            worksheet = root.find('.//ss:Worksheet', ns)
            if worksheet is None:
                print("Error: Could not find worksheet in XML file")
                return False
                
            table = worksheet.find('.//ss:Table', ns)
            if table is None:
                print("Error: Could not find table in worksheet")
                return False
            
            rows = table.findall('ss:Row', ns)
            if len(rows) < 2:
                print("Error: Not enough data rows in table")
                return False
            
            # Parse dates from first row
            self._parse_dates(rows[0], ns)
            
            # Parse user data from subsequent rows
            self._parse_user_data(rows[1:], ns)
            
            return True
            
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def _parse_dates(self, row, ns):
        """Extract dates from the header row"""
        cells = row.findall('ss:Cell', ns)
        for cell in cells:
            data = cell.find('ss:Data', ns)
            if data is not None and data.text:
                # Check if it looks like a date (contains dots)
                if '.' in data.text:
                    self.dates.append(data.text.strip())
    
    def _parse_user_data(self, rows, ns):
        """Extract user data from data rows"""
        for i, row in enumerate(rows):
            cells = row.findall('ss:Cell', ns)
            if not cells:
                continue
                
            # Get first cell data (username or label)
            first_cell = cells[0].find('ss:Data', ns)
            if first_cell is None or not first_cell.text:
                continue
                
            first_text = first_cell.text.strip()
            
            # Skip empty rows
            if not first_text:
                continue
            
            # Only process user data rows (no more MVP row to handle)
            if self._is_user_row(cells, ns):
                self._parse_user_row(first_text, cells, ns)
        
        # After parsing all users, calculate MVP for each day
        self._calculate_daily_mvp()
    
    def _calculate_daily_mvp(self):
        """Calculate MVP (highest scorer) for each day"""
        self.mvp_data = {}
        
        for day_idx in range(len(self.dates)):
            max_score = -1
            mvp_users = []
            
            # Find the highest score for this day
            for username, scores in self.users_data.items():
                if day_idx < len(scores):
                    score = scores[day_idx]
                    if score > max_score:
                        max_score = score
                        mvp_users = [username]
                    elif score == max_score and score > 0:
                        mvp_users.append(username)
            
            # Set MVP for this day (handle ties with "|")
            if mvp_users and max_score > 0:
                self.mvp_data[day_idx] = "|".join(mvp_users)
            else:
                self.mvp_data[day_idx] = "-"
    
    def _is_user_row(self, cells, ns) -> bool:
        """Check if this row contains user score data"""
        # Check if we have numeric-like data in subsequent cells
        for cell in cells[1:]:
            data = cell.find('ss:Data', ns)
            if data is not None and data.text:
                try:
                    int(data.text)
                    return True
                except ValueError:
                    continue
        return False
    
    def _parse_user_row(self, username: str, cells, ns):
        """Parse individual user data row"""
        user_scores = []
        
        # Extract daily scores from cells (skip first cell which is username)
        for i in range(len(self.dates)):
            if i + 1 < len(cells):  # +1 because cell 0 is username
                cell = cells[i + 1]
                data = cell.find('ss:Data', ns)
                if data is not None and data.text:
                    try:
                        score = int(data.text)
                        user_scores.append(score)
                    except ValueError:
                        user_scores.append(0)
                else:
                    user_scores.append(0)
            else:
                user_scores.append(0)
        
        self.users_data[username] = user_scores
        self.totals[username] = sum(user_scores)
    
    def generate_html(self, output_file: str = 'index.html'):
        """Generate beautiful HTML page from parsed data"""
        
        # Sort users by total score
        sorted_users = sorted(self.totals.items(), key=lambda x: x[1], reverse=True)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍅 Pomodoro Leaderboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="80" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="60" r="1" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
        }}
        
        .header h1 {{
            font-size: 3em;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
            margin-top: 10px;
            position: relative;
            z-index: 1;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 40px;
            text-align: center;
        }}
        
        .summary h2 {{
            color: #2d3436;
            margin-bottom: 20px;
            font-size: 2em;
        }}
        
        .podium {{
            display: flex;
            justify-content: center;
            align-items: end;
            gap: 20px;
            margin: 30px 0;
            flex-wrap: wrap;
        }}
        
        .podium-place {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            min-width: 150px;
            position: relative;
        }}
        
        .podium-place.first {{
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            transform: scale(1.1);
            order: 2;
        }}
        
        .podium-place.second {{
            background: linear-gradient(135deg, #c0c0c0 0%, #dcdcdc 100%);
            order: 1;
        }}
        
        .podium-place.third {{
            background: linear-gradient(135deg, #cd7f32 0%, #daa520 100%);
            order: 3;
        }}
        
        .podium-rank {{
            font-size: 2em;
            font-weight: bold;
            color: white;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .podium-name {{
            font-size: 1.2em;
            font-weight: bold;
            margin: 10px 0;
            color: #2d3436;
        }}
        
        .podium-score {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2d3436;
        }}
        
        .leaderboard-table {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 40px;
        }}
        
        .table-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            font-size: 1.5em;
            font-weight: bold;
            text-align: center;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: bold;
            color: #2d3436;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .user-name {{
            font-weight: bold;
            color: #2d3436;
            text-align: left;
            position: sticky;
            left: 0;
            background: white;
            z-index: 5;
        }}
        
        .score-cell {{
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .score-cell:hover {{
            background: #e3f2fd;
            transform: scale(1.05);
        }}
        
        .score-high {{
            background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
            color: white;
            border-radius: 8px;
        }}
        
        .score-medium {{
            background: linear-gradient(135deg, #ff9800 0%, #ffc107 100%);
            color: white;
            border-radius: 8px;
        }}
        
        .score-low {{
            background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
            color: white;
            border-radius: 8px;
        }}
        
        .total-column {{
            background: #f0f8ff !important;
            font-weight: bold;
            font-size: 1.2em;
            color: #1976d2;
            position: sticky;
            left: 120px;
            z-index: 5;
        }}
        
        .mvp-row {{
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        }}
        
        .mvp-cell {{
            color: #e65100;
            font-weight: bold;
            font-style: italic;
        }}
        
        .rank-1 {{ color: #ffd700; font-weight: bold; }}
        .rank-2 {{ color: #c0c0c0; font-weight: bold; }}
        .rank-3 {{ color: #cd7f32; font-weight: bold; }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: #667eea;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #636e72;
            font-size: 1.1em;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2em; }}
            .content {{ padding: 20px; }}
            .podium {{ flex-direction: column; align-items: center; }}
            .podium-place {{ margin-bottom: 10px; }}
            th, td {{ padding: 10px 8px; font-size: 0.9em; }}
            
            /* Disable sticky positioning on mobile to prevent interference */
            .user-name {{
                position: static;
                background: white;
            }}
            
            .total-column {{
                position: static;
                background: #f0f8ff !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍅 Pomodoro Leaderboard</h1>
            <p>Daily productivity tracking and rankings</p>
        </div>
        
        <div class="content">
"""
        
        # Add summary section
        html_content += self._generate_summary_section(sorted_users)
        
        # Add main leaderboard table
        html_content += self._generate_leaderboard_table()
        
        # Add statistics
        html_content += self._generate_statistics()
        
        html_content += """
        </div>
    </div>
    
    <script>
        // Add interactive features
        document.addEventListener('DOMContentLoaded', function() {
            // Highlight score cells on hover
            const scoreCells = document.querySelectorAll('.score-cell');
            scoreCells.forEach(cell => {
                cell.addEventListener('mouseenter', function() {
                    this.style.transform = 'scale(1.1)';
                });
                cell.addEventListener('mouseleave', function() {
                    this.style.transform = 'scale(1)';
                });
            });
        });
    </script>
</body>
</html>"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML leaderboard generated successfully: {output_file}")
    
    def _generate_summary_section(self, sorted_users):
        """Generate the summary/podium section"""
        html = """
            <div class="summary">
                <h2>🏆 Current Rankings</h2>
                <div class="podium">
        """
        
        podium_classes = ['first', 'second', 'third']
        ranks = ['🥇', '🥈', '🥉']
        
        for i, (username, total) in enumerate(sorted_users[:3]):
            class_name = podium_classes[i] if i < 3 else ''
            rank_emoji = ranks[i] if i < 3 else f"#{i+1}"
            
            html += f"""
                    <div class="podium-place {class_name}">
                        <div class="podium-rank">{rank_emoji}</div>
                        <div class="podium-name">{username}</div>
                        <div class="podium-score">{total} 🍅</div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        """
        
        return html
    
    def _generate_leaderboard_table(self):
        """Generate the main leaderboard table"""
        html = """
            <div class="leaderboard-table">
                <div class="table-header">📊 Daily Tracking</div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th class="user-name">User</th>
                                <th class="total-column">Total 🍅</th>
        """
        
        # Add date headers in reverse order (most recent first)
        for date in reversed(self.dates):
            html += f'<th>{date}</th>'
        
        html += '</tr></thead><tbody>'
        
        # Sort users by total score for ranking
        sorted_users = sorted(self.totals.items(), key=lambda x: x[1], reverse=True)
        
        # Add user rows
        for rank, (username, total) in enumerate(sorted_users, 1):
            rank_class = f'rank-{rank}' if rank <= 3 else ''
            html += f'<tr><td class="user-name {rank_class}">#{rank} {username}</td>'
            html += f'<td class="total-column">{total}</td>'
            
            user_scores = self.users_data.get(username, [])
            max_score = max(user_scores) if user_scores else 0
            
            # Display scores in reverse order (most recent first)
            for i in reversed(range(len(user_scores))):
                score = user_scores[i]
                score_class = 'score-cell'
                if score > 0:
                    if max_score > 0:
                        if score >= max_score * 0.8:
                            score_class += ' score-high'
                        elif score >= max_score * 0.4:
                            score_class += ' score-medium'
                        else:
                            score_class += ' score-low'
                
                html += f'<td class="{score_class}">{score}</td>'
            
            html += '</tr>'
        
        # Add MVP row
        html += '<tr class="mvp-row"><td class="user-name"><strong>👑 MVP</strong></td>'
        html += '<td class="mvp-cell">-</td>'
        # Display MVP data in reverse order (most recent first)
        for i in reversed(range(len(self.dates))):
            mvp = self.mvp_data.get(i, '')
            html += f'<td class="mvp-cell">{mvp}</td>'
        html += '</tr>'
        
        html += '</tbody></table></div></div>'
        
        return html
    
    def _generate_statistics(self):
        """Generate statistics section"""
        total_pomodoros = sum(self.totals.values())
        active_days = len([d for d in self.dates if d])
        avg_per_day = round(total_pomodoros / active_days, 1) if active_days > 0 else 0
        top_performer = max(self.totals.items(), key=lambda x: x[1])[0] if self.totals else "N/A"
        
        html = f"""
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{total_pomodoros}</div>
                    <div class="stat-label">Total Pomodoros</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{active_days}</div>
                    <div class="stat-label">Tracking Days</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_per_day}</div>
                    <div class="stat-label">Avg per Day</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">👑</div>
                    <div class="stat-label">Leader: {top_performer}</div>
                </div>
            </div>
        """
        
        return html


def main():
    parser = argparse.ArgumentParser(description='Convert Pomodoro leaderboard XML to HTML')
    parser.add_argument('input_file', help='Input XML file path')
    parser.add_argument('-o', '--output', default='index.html', 
                       help='Output HTML file path (default: index.html)')
    
    args = parser.parse_args()
    
    # Create parser instance
    leaderboard = PomodoroLeaderboardParser(args.input_file)
    
    # Parse XML data
    if not leaderboard.parse_xml():
        sys.exit(1)
    
    # Generate HTML
    leaderboard.generate_html(args.output)
    
    print(f"\n📊 Leaderboard Summary:")
    print(f"   📅 Days tracked: {len(leaderboard.dates)}")
    print(f"   👥 Users: {len(leaderboard.users_data)}")
    print(f"   🍅 Total pomodoros: {sum(leaderboard.totals.values())}")
    print(f"\n🏆 Top performers:")
    
    sorted_users = sorted(leaderboard.totals.items(), key=lambda x: x[1], reverse=True)
    for rank, (user, total) in enumerate(sorted_users[:3], 1):
        emoji = ['🥇', '🥈', '🥉'][rank-1]
        print(f"   {emoji} {user}: {total} pomodoros")


if __name__ == '__main__':
    main()