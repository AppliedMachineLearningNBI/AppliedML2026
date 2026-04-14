import os
import yaml
import math
from typing import Dict, List, Tuple, Optional

class SolutionChecker:
    """
    Solution checker for verifying student submissions against expected format and constraints.

    Key Features:
    - Organizes and validates student submission files, ensuring correct structure and content.
    - Checks for the presence and validity of required files: description, variable lists, and prediction outputs.
    - Enforces constraints on allowed variables, variable counts, and prediction formats for each problem type.
    - Provides detailed error handling and reporting through dedicated error-handling methods (all methods with 'error' in their name are responsible for error tracking, reporting, and summarization).

    To future TAs:
    You will likely need to modify the __init__ method
    - Change the allowed variables in `self.class_vars`, `self.reg_vars`, and `self.clustering_vars` as needed
    - Adjust the `self.max_variables` dictionary to set limits on the number of variables for each problem type
    - Update the `self.test_entries` dictionary to specify the expected number of entries for each problem type
    - Modify the `self.prediction_range` dictionary to set the valid range for predictions for each problem type

    Structure: 
    - read_filenames: Reads filenames and organizes them by student and problem type.
    - verify_file_structure: Checks if all required files are present for each student.
    - verify_description_files: Validates that each student has exactly one valid description file.
    - verify_variable_lists: Validates variable lists against allowed variables and limits.
    - verify_solution_files: Checks solution files for correct format and number of predictions.
    - check_solutions: Main method to run all checks and return results.

     Error Handling:
    - Methods with 'error' in their name (write_error, print_suppressed_errors_summary, reset_error_counters) are dedicated to error handling, including tracking, limiting, and summarizing error messages to avoid overwhelming output.
    """
    
    def __init__(self, max_errors: int = 5, config_path: str = None):
        self.max_errors = max_errors
        self.errors = 0
        self.all_errors = 0
        self.suppressed_errors = 0

        if config_path is None:
            # Find the project root (where main.py is)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(os.path.dirname(base_dir), 'config', 'file_formats.yaml')

        # Load config
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config file '{config_path}': {e}")

        self.class_vars = config["class_vars"]
        self.reg_vars = config.get("reg_vars", self.class_vars)
        self.clustering_vars = config["clustering_vars"]
        self.all_variables = self.class_vars + self.reg_vars + self.clustering_vars

        self.max_variables = config["max_variables"]
        self.test_entries = config["test_entries"]

        # Convert prediction_range values
        self.prediction_range = {}
        for k, v in config["prediction_range"].items():
            min_val, max_val = v
            min_val = float("-inf") if min_val in ("-inf", -math.inf) else float(min_val)
            max_val = float("inf") if max_val in ("inf", math.inf) else float(max_val)
            self.prediction_range[k] = (min_val, max_val)

    def write_error(self, msg: str) -> bool:
        """
        Write error message with a cap on total messages per check phase.
        
        Args:
            msg: Error message to display
            
        Returns:
            True if error was printed, False if suppressed due to cap
        """
        if self.errors < self.max_errors:
            print(f"ERROR: {msg}")
            self.errors += 1
            return True
        else:
            self.suppressed_errors += 1
            return False

    def print_suppressed_errors_summary(self):
        """Print summary of suppressed errors if any were suppressed."""
        if self.suppressed_errors > 0:
            print(f"NOTE: {self.suppressed_errors} additional error(s) were suppressed. "
                  f"Please fix the errors shown above first, then re-run to see remaining errors.")

    def reset_error_counters(self):
        """Reset error counters for a new check phase."""
        self.errors = 0
        self.suppressed_errors = 0

    def init_entry(self) -> Dict:
        """Initialize entry structure for a student."""
        return {
            'Classification': {},
            'Regression': {},
            'Clustering': {}
        }

    def read_filenames(self, directory: str) -> Dict:
        """
        Read and organize filenames from student subdirectories.
        
        Args:
            directory: Path to the solutions directory containing student subdirectories
            
        Returns:
            Dictionary organized by student_directory -> problem_type -> implementation -> files
        """
        tmp = {}
        self.reset_error_counters()
        
        if not os.path.exists(directory):
            self.write_error(f"Directory {directory} does not exist")
            return tmp
        
        # Iterate through each subdirectory in the solutions directory
        for student_dir in os.listdir(directory):
            student_path = os.path.join(directory, student_dir)
            
            # Skip if not a directory
            if not os.path.isdir(student_path):
                print(f"Skipping {student_dir} as it is not a directory.")
                continue
            
            # Initialize entry for this student directory
            tmp[student_dir] = self.init_entry()
            
            # Process files in the student directory
            for filename in os.listdir(student_path):
                file_path = os.path.join(student_path, filename)
                
                # Skip non-files
                if not os.path.isfile(file_path):
                    continue
                
                # Handle CSV files
                if filename.lower().endswith('.csv'):
                    self._process_csv_file(filename, file_path, student_dir, tmp)
                
                # Handle TXT files (description files)
                elif filename.lower().endswith('.txt'):
                    # Store description file path for later verification
                    if 'description_files' not in tmp[student_dir]:
                        tmp[student_dir]['description_files'] = []
                    tmp[student_dir]['description_files'].append(file_path)
        
        self.print_suppressed_errors_summary()
        self.all_errors += self.errors
        return tmp

    def _process_csv_file(self, filename: str, file_path: str, student_dir: str, tmp: Dict):
        """
        Process a CSV file and add it to the appropriate structure.
        
        Args:
            filename: Name of the CSV file
            file_path: Full path to the CSV file
            student_dir: Student directory name
            tmp: Dictionary to store the file information
        """
        splitted = filename.split('_')
        
        # Check if it's a variable list file
        is_varlist = filename.lower().endswith('_variablelist.csv')
        
        if is_varlist:
            # Format: ProblemType_[...]_Algo_VariableList.csv
            if len(splitted) < 3:
                self.write_error(
                    f"Variable list filename '{filename}' in {student_dir} does not match expected format "
                    f"'ProblemType_[...]_Algo_VariableList.csv'"
                )
                return
            
            project_part = splitted[0]
            # Algorithm name is the second-to-last part (before VariableList)
            implementation = splitted[-2]
        else:
            # Format: ProblemType_[...]_Algo.csv
            if len(splitted) < 2:
                self.write_error(
                    f"Prediction filename '{filename}' in {student_dir} does not match expected format "
                    f"'ProblemType_[...]_Algo.csv'"
                )
                return
            
            project_part = splitted[0]
            # Algorithm name is the last part (before .csv)
            implementation = splitted[-1].split('.csv')[0]
        
        # Validate problem type
        if project_part not in ['Classification', 'Regression', 'Clustering']:
            self.write_error(
                f"Filename '{filename}' in {student_dir} contains invalid problem type '{project_part}'. "
                f"Expected: Classification, Regression, or Clustering."
            )
            return
        
        # Initialize implementation entry if needed
        if implementation not in tmp[student_dir][project_part]:
            tmp[student_dir][project_part][implementation] = {}
        
        # Store file path
        if is_varlist:
            tmp[student_dir][project_part][implementation]['vars'] = file_path
        else:
            tmp[student_dir][project_part][implementation]['preds'] = file_path

    def verify_file_structure(self, names: Dict) -> bool:
        """
        Verify that all required files are present for each student.
        
        Args:
            names: Dictionary from read_filenames()
            
        Returns:
            True if all structures are valid, False otherwise
        """
        self.reset_error_counters()
        structure_valid = True
        
        for student_dir, parts in names.items():
            print(f'{student_dir}:')
            
            # Check for description files
            if 'description_files' not in parts:
                self.write_error(f'    No description file (.txt) found in {student_dir}')
                structure_valid = False
            elif len(parts['description_files']) == 0:
                self.write_error(f'    No description file (.txt) found in {student_dir}')
                structure_valid = False
            elif len(parts['description_files']) > 1:
                self.write_error(f'    Multiple description files found in {student_dir}: {parts["description_files"]}')
                structure_valid = False
            else:
                print(f'    ✓ Description file: {os.path.basename(parts["description_files"][0])}')
            
            # Check problem types and implementations
            for part in ['Classification', 'Regression', 'Clustering']:
                print(f'    {part}:')
                if part not in parts or len(parts[part]) == 0:
                    self.write_error(f'        {part} does not have any files in {student_dir}')
                    structure_valid = False
                else:
                    for implementation, files in parts[part].items():
                        missing_files = []
                        if 'vars' not in files:
                            missing_files.append('VariableList')
                        if 'preds' not in files:
                            missing_files.append('Predictions')
                        
                        if missing_files:
                            self.write_error(
                                f"            {implementation} is missing: {', '.join(missing_files)} in {student_dir}"
                            )
                            structure_valid = False
                        else:
                            print(f'        {implementation}:')
                            print(f'            preds: {os.path.basename(files["preds"])}')
                            print(f'            vars:  {os.path.basename(files["vars"])}')

        if self.errors == 0:
            print('File structure verified successfully')
        else:
            print(f'File structure verification had {self.errors} errors')
            
        self.print_suppressed_errors_summary()
        self.all_errors += self.errors
        return structure_valid

    def verify_description_files(self, names: Dict) -> bool:
        """
        Verify that each student has exactly one valid description file (.txt).
        
        Args:
            names: Dictionary from read_filenames()
            
        Returns:
            True if all students have valid description files, False otherwise
        """
        self.reset_error_counters()
        descriptions_valid = True
        
        for student_dir, parts in names.items():
            if 'description_files' not in parts or len(parts['description_files']) != 1:
                # This was already checked in verify_file_structure
                descriptions_valid = False
                continue
            
            desc_file = parts['description_files'][0]
            try:
                with open(desc_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        self.write_error(f"Description file in {student_dir} is empty. "
                                       f"Please provide a description of your solution.")
                        descriptions_valid = False
                    else:
                        print(f"✓ Description file verified for {student_dir}")
            except Exception as e:
                self.write_error(f"Error reading description file in {student_dir}: {str(e)}")
                descriptions_valid = False
        
        if self.errors == 0:
            print('Description files verified successfully')
        else:
            print(f'Description file verification had {self.errors} errors')
            
        self.print_suppressed_errors_summary()
        self.all_errors += self.errors
        return descriptions_valid

    def verify_variable_lists(self, names: Dict) -> bool:
        """
        Verify that variable lists contain only allowed variables and don't exceed limits.
        
        Args:
            names: Dictionary from read_filenames()
            
        Returns:
            True if all variable lists are valid, False otherwise
        """
        self.reset_error_counters()
        variables_valid = True
        
        for student_dir, parts in names.items():
            for part in ['Classification', 'Regression', 'Clustering']:
                if part not in parts:
                    continue
                    
                for implementation, files in parts[part].items():
                    if 'vars' not in files:
                        continue
                        
                    file_path = files['vars']
                    count = 0
                    
                    try:
                        with open(file_path, 'r') as f:
                            for line_num, line in enumerate(f, 1):
                                var_name = line.strip()
                                if var_name == "":
                                    print(f"Skipping empty line {line_num} in {part} file: {file_path}")
                                    continue
                                if var_name.endswith(","):
                                    var_name = var_name[:-1]
                                if var_name not in self.all_variables:
                                    self.write_error(
                                        f"Variable '{var_name}' not in allowed list. File: {student_dir}/{os.path.basename(file_path)}"
                                    )
                                    variables_valid = False
                                else:
                                    count += 1
                                    
                        if count > self.max_variables[part]:
                            self.write_error(
                                f'Too many variables ({count}/{self.max_variables[part]}) for {part} in {student_dir}/{os.path.basename(file_path)}'
                            )
                            variables_valid = False
                            
                    except FileNotFoundError:
                        self.write_error(f"Variable list file not found: {student_dir}/{os.path.basename(file_path)}")
                        variables_valid = False
                    except Exception as e:
                        self.write_error(f"Error reading variable list {student_dir}/{os.path.basename(file_path)}: {str(e)}")
                        variables_valid = False
                        
        if self.errors == 0:
            print('Variables parsed without error')
        else:
            print(f'Variables had {self.errors} errors')
            
        self.print_suppressed_errors_summary()
        self.all_errors += self.errors
        return variables_valid

    def verify_solution_files(self, names: Dict) -> bool:
        """
        Verify that solution files have correct format and number of predictions.
        
        Args:
            names: Dictionary from read_filenames()
            
        Returns:
            True if all solution files are valid, False otherwise
        """
        self.reset_error_counters()
        solutions_valid = True
        
        for student_dir, parts in names.items():
            for part in ['Classification', 'Regression', 'Clustering']:
                if part not in parts:
                    continue
                    
                for implementation, files in parts[part].items():
                    if 'preds' not in files:
                        continue
                        
                    file_path = files['preds']
                    
                    try:
                        with open(file_path, 'r') as f:
                            lines = [line for line in f]
                            
                        for i, line in enumerate(lines):
                            if ',' in line:
                                try:
                                    index, value = line.strip().split(',')
                                except ValueError:
                                    self.write_error(
                                        f"Expected index,value format at line {i+1} in {student_dir}/{os.path.basename(file_path)}: {line.strip()}"
                                    )
                                    solutions_valid = False
                                    continue
                                    
                                try:
                                    if int(index) != i:
                                        self.write_error(
                                            f'Incorrect index at line {i+1} in {student_dir}/{os.path.basename(file_path)}: expected {i}, got {index}'
                                        )
                                        solutions_valid = False
                                except ValueError:
                                    self.write_error(
                                        f'Invalid index format in {student_dir}/{os.path.basename(file_path)}: {index}'
                                    )
                                    solutions_valid = False
                            else:
                                value = line.strip()
                                
                            try:
                                value = float(value)
                            except ValueError:
                                self.write_error(
                                    f"Invalid number at line {i+1} in {student_dir}/{os.path.basename(file_path)}: {value}"
                                )
                                solutions_valid = False
                                continue
                            
                            if part == 'Clustering':
                                if not value.is_integer():
                                    self.write_error(
                                        f'Clustering value must be integer at line {i+1} in {student_dir}/{os.path.basename(file_path)}: {value}'
                                    )
                                    solutions_valid = False
                                    continue
                                    
                            mi, ma = self.prediction_range[part]
                            if not (mi <= value <= ma):
                                self.write_error(
                                    f'Value out of range ({mi},{ma}) at line {i+1} in {student_dir}/{os.path.basename(file_path)}: {value}'
                                )
                                solutions_valid = False
                                
                        # Check number of predictions
                        expected_entries = self.test_entries[part]
                        if len(lines) != expected_entries:
                            self.write_error(
                                f'Wrong number of predictions for {part} in {student_dir}/{os.path.basename(file_path)}: got {len(lines)}, expected {expected_entries}'
                            )
                            solutions_valid = False
                            
                    except FileNotFoundError:
                        self.write_error(f"Solution file not found: {student_dir}/{os.path.basename(file_path)}")
                        solutions_valid = False
                    except Exception as e:
                        self.write_error(f"Error reading solution file {student_dir}/{os.path.basename(file_path)}: {str(e)}")
                        solutions_valid = False
                        
        if self.errors == 0:
            print('Solutions parsed without error')
        else:
            print(f'Solutions had {self.errors} errors')
            
        self.print_suppressed_errors_summary()
        self.all_errors += self.errors
        return solutions_valid

    def check_solutions(self, directory: str) -> Tuple[bool, Dict, List[str]]:
        """
        Main method to check all solutions in a directory.
        
        Args:
            directory: Path to directory containing student subdirectories
            
        Returns:
            Tuple of (all_valid, parsed_solutions, error_messages)
        """
        print(f"Checking solutions in directory: {directory}")
        
        # Reset error counters
        self.all_errors = 0
        
        # Step 1: Read and parse filenames from subdirectories
        names = self.read_filenames(directory)
        if not names:
            return False, {}, ["No valid solution directories found"]
        
        # Step 2: Verify file structure
        structure_valid = self.verify_file_structure(names)
        
        # Step 3: Verify description files
        descriptions_valid = self.verify_description_files(names)
        
        # Step 4: Verify variable lists
        variables_valid = self.verify_variable_lists(names)
        
        # Step 5: Verify solution files
        solutions_valid = self.verify_solution_files(names)
        
        # Final check
        all_valid = structure_valid and descriptions_valid and variables_valid and solutions_valid
        
        if self.all_errors == 0:
            print('All submissions had no errors')
        else:
            print(f'Found {self.all_errors} total errors across all submissions')
            
        return all_valid, names, []

    def student_friendly_check(self, directory: str):
        """
        Allows students to check whether their solution directory has the required format.
        Prints clear messages about any problems found.

        Args:
            directory: Path to the directory containing all solution and description files for a single student.
        """
        print(f"\n=== Checking your submission in: {directory} ===\n")
        if not os.path.isdir(directory):
            print(f"❌ The path '{directory}' is not a directory or does not exist.")
            return

        # Simulate the structure expected by the rest of the checker
        student_dir = os.path.basename(os.path.normpath(directory))
        names = {student_dir: self.init_entry()}

        # Scan files in the directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if not os.path.isfile(file_path):
                continue

            # CSV files
            if filename.lower().endswith('.csv'):
                self._process_csv_file(filename, file_path, student_dir, names)
            # TXT files (description)
            elif filename.lower().endswith('.txt'):
                if 'description_files' not in names[student_dir]:
                    names[student_dir]['description_files'] = []
                names[student_dir]['description_files'].append(file_path)

        print("\n--- Checking file structure ---")
        structure_valid = self.verify_file_structure(names)
        if not structure_valid:
            print("❌ There are problems with your file structure. Please fix the above issues and try again.\n")
        else:
            print("✅ File structure looks good!\n")

        print("\n--- Checking description file(s) ---")
        descriptions_valid = self.verify_description_files(names)
        if not descriptions_valid:
            print("❌ There are problems with your description file. Please fix the above issues and try again.\n")
        else:
            print("✅ Description file looks good!\n")

        print("\n--- Checking variable lists ---")
        variables_valid = self.verify_variable_lists(names)
        if not variables_valid:
            print("❌ There are problems with your variable lists. Please fix the above issues and try again.\n")
        else:
            print("✅ Variable lists look good!\n")

        print("\n--- Checking prediction/solution files ---")
        solutions_valid = self.verify_solution_files(names)
        if not solutions_valid:
            print("❌ There are problems with your prediction/solution files. Please fix the above issues and try again.\n")
        else:
            print("✅ Prediction/solution files look good!\n")

        all_valid = structure_valid and descriptions_valid and variables_valid and solutions_valid
        if all_valid:
            print("\n🎉 Your submission passes all format checks! Good luck!")
        else:
            print("\n⚠️ Please fix the above issues and re-run this check before submitting.")
            
def check_student_solutions(directory: str, max_errors: int = 5) -> Tuple[bool, Dict, List[str]]:
    """
    Convenience function to check student solutions.
    
    Args:
        directory: Path to directory containing student subdirectories
        max_errors: Maximum number of errors to display before stopping
        
    Returns:
        Tuple of (all_valid, parsed_solutions, error_messages)
    """
    checker = SolutionChecker(max_errors=max_errors)
    return checker.check_solutions(directory)