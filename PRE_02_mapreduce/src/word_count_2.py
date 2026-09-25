import glob
import os.path
import string
import time

DATA_FOLDER = "PRE_02_mapreduce/data"
INPUT_FOLDER = "PRE_02_mapreduce/temp/input"
OUTPUT_FOLDER = "PRE_02_mapreduce/temp/output"


# Manejo de carpetas
# -----------------------------------------------------------------------------


def initialize_folder(folder):
    """Crea la carpeta si no existe, o la vacia si ya existe."""
    if os.path.exists(folder):
        for file in glob.glob(f"{folder}/*"):
            os.remove(file)
    else:
        os.makedirs(folder)


def delete_folder(folder):
    """Borra la carpeta y su contenido si existe."""
    if os.path.exists(folder):
        for file in glob.glob(f"{folder}/*"):
            os.remove(file)
        os.rmdir(folder)


# Genera copias de los archivos en data/
# -----------------------------------------------------------------------------


def generate_file_copies(n, data_folder=DATA_FOLDER, input_folder=INPUT_FOLDER):
    for file in glob.glob(f"{data_folder}/*"):

        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        raw_filename_with_extension = os.path.basename(file)
        raw_filename_without_extension = os.path.splitext(raw_filename_with_extension)[
            0
        ]

        for i in range(1, n + 1):
            new_filename = f"{raw_filename_without_extension}_{i:05d}.txt"
            with open(f"{input_folder}/{new_filename}", "w", encoding="utf-8") as f2:
                f2.write(text)


# Lectura de los archivos
# -----------------------------------------------------------------------------


def read_all_lines(input_folder):
    sequence = []
    for file in glob.glob(f"{input_folder}/*"):
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                sequence.append((file, line))
    return sequence


# Mapper
# -----------------------------------------------------------------------------


def mapper(sequence):
    pairs_sequence = []
    for _, line in sequence:
        line = line.lower()
        line = line.translate(str.maketrans("", "", string.punctuation))
        line = line.replace("\n", "")
        words = line.split()
        pairs_sequence.extend([(word, 1) for word in words])
    return pairs_sequence


# Shuffle and sort
# -----------------------------------------------------------------------------


def shuffle_and_sort(pairs_sequence):
    return sorted(pairs_sequence)


# Reducer
# -----------------------------------------------------------------------------


def reducer(pairs_sequence):
    result = []
    for key, value in pairs_sequence:
        if result and result[-1][0] == key:
            result[-1] = (key, result[-1][1] + value)
        else:
            result.append((key, value))
    return result


# Escritura de resultados
# -----------------------------------------------------------------------------


def create_output_folder(output_folder):
    if os.path.exists(output_folder):
        raise FileExistsError(f"The folder '{output_folder}' already exists.")
    os.makedirs(output_folder)


def save_output(output_folder, result):
    with open(f"{output_folder}/part-00000", "w", encoding="utf-8") as f:
        for key, value in result:
            f.write(f"{key}\t{value}\n")


def create_marker(output_folder):
    with open(f"{output_folder}/_SUCCESS", "w", encoding="utf-8") as f:
        f.write("")


# Orquestador
# -----------------------------------------------------------------------------


def hadoop(input_folder, output_folder, mapper_fn, reducer_fn):
    sequence = read_all_lines(input_folder)
    pairs_sequence = mapper_fn(sequence)
    pairs_sequence = shuffle_and_sort(pairs_sequence)
    result = reducer_fn(pairs_sequence)
    create_output_folder(output_folder)
    save_output(output_folder, result)
    create_marker(output_folder)


if __name__ == "__main__":

    initialize_folder(INPUT_FOLDER)
    delete_folder(OUTPUT_FOLDER)
    generate_file_copies(1000)

    start_time = time.time()

    hadoop(
        input_folder=INPUT_FOLDER,
        output_folder=OUTPUT_FOLDER,
        mapper_fn=mapper,
        reducer_fn=reducer,
    )

    end_time = time.time()
    print(f"Tiempo de ejecución: {end_time - start_time:.2f} segundos")
