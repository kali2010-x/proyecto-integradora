# Compila el esclavo simulado contra wolfSSL instalado en el sistema (o en WOLF=ruta).
WOLF ?= /usr/local
FRAME_SIZE ?= 128
SRC = esclavo_sim.c ../esp32/firmware/main/enlace.c ../esp32/firmware/main/cliente_tls.c
esclavo_sim: $(SRC)
	gcc -O2 -Wall -DFRAME_SIZE=$(FRAME_SIZE) -I../esp32/firmware/main -I$(WOLF)/include $(SRC) \
	    -L$(WOLF)/lib -Wl,-rpath,$(WOLF)/lib -lwolfssl -lpthread -o $@
clean:
	rm -f esclavo_sim
