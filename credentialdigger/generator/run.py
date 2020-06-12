from generator import Generator
import time

generator = Generator(save_model_path='./',
                      training_data_size=75000,
                      states_n=13,
                      actions_n=12,
                      alpha=0.5,
                      gamma=0.85,
                      epochs_basis=50,
                      max_length=150)

corpus = ['int main(){\n\t\treturn 0;\n}' for i in range(150)]
start = time.time()
generator.train_model(corpus)
print(time.time() - start)
