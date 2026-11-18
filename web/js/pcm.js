// Captura mono a 16 kHz. Envia um bloco a cada 64 ms.
class CapturaPCM extends AudioWorkletProcessor {
  buffer = new Int16Array(1024);
  pos = 0;
  energia = 0;
  process(inputs) {
    for (const valor of inputs[0]?.[0] || []) {
      this.buffer[this.pos++] = Math.max(-1, Math.min(1, valor)) * 32767;
      this.energia += valor * valor;
      if (this.pos === this.buffer.length) {
        this.port.postMessage({ pcm: this.buffer, rms: Math.sqrt(this.energia / this.pos) }, [this.buffer.buffer]);
        this.buffer = new Int16Array(1024);
        this.pos = this.energia = 0;
      }
    }
    return true;
  }
}
registerProcessor("captura-pcm", CapturaPCM);
