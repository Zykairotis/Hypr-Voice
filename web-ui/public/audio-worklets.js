class AudioLevelWorkletProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.peak = 0;
    this.rms = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input.length > 0) {
      const channelData = input[0];

      let peak = 0;
      let sum = 0;
      for (let i = 0; i < channelData.length; i++) {
        const abs = Math.abs(channelData[i]);
        peak = Math.max(peak, abs);
        sum += channelData[i] * channelData[i];
      }

      const rms = Math.sqrt(sum / channelData.length);

      this.port.postMessage({
        peak: peak,
        rms: rms,
        timestamp: currentTime
      });
    }

    return true;
  }
}

registerProcessor('audio-level-processor', AudioLevelWorkletProcessor);

class AudioFrequencyProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.fftSize = 2048;
    this.frequencyData = new Float32Array(this.fftSize);
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input.length > 0) {
      const channelData = input[0];

      this.port.postMessage({
        frequencyData: channelData,
        timestamp: currentTime
      });
    }

    return true;
  }
}

registerProcessor('audio-frequency-processor', AudioFrequencyProcessor);

class NoiseReductionProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.noiseProfile = new Float32Array(2048);
    this.reductionAmount = 0.5;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const output = outputs[0];

    if (input.length > 0 && output.length > 0) {
      for (let channel = 0; channel < output.length; channel++) {
        const inputChannel = input[channel];
        const outputChannel = output[channel];

        for (let i = 0; i < inputChannel.length; i++) {
          outputChannel[i] = inputChannel[i] * (1 - this.reductionAmount);
        }
      }
    }

    return true;
  }
}

registerProcessor('noise-reduction-processor', NoiseReductionProcessor);

class AudioCompressorProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.threshold = 0.5;
    this.ratio = 4.0;
    this.attack = 0.003;
    this.release = 0.25;
    this.envelope = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const output = outputs[0];

    if (input.length > 0 && output.length > 0) {
      for (let channel = 0; channel < output.length; channel++) {
        const inputChannel = input[channel];
        const outputChannel = output[channel];

        for (let i = 0; i < inputChannel.length; i++) {
          const inputLevel = Math.abs(inputChannel[i]);

          if (inputLevel > this.threshold) {
            const excess = inputLevel - this.threshold;
            const compressedExcess = excess / this.ratio;
            const outputLevel = this.threshold + compressedExcess;

            const gain = outputLevel / inputLevel;
            outputChannel[i] = inputChannel[i] * gain;
          } else {
            outputChannel[i] = inputChannel[i];
          }
        }
      }
    }

    return true;
  }
}

registerProcessor('audio-compressor-processor', AudioCompressorProcessor);

class AudioNormalizerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.peak = 0;
    this.smoothing = 0.99;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const output = outputs[0];

    if (input.length > 0 && output.length > 0) {
      let currentPeak = 0;

      for (let channel = 0; channel < output.length; channel++) {
        const inputChannel = input[channel];
        const outputChannel = output[channel];

        for (let i = 0; i < inputChannel.length; i++) {
          const abs = Math.abs(inputChannel[i]);
          currentPeak = Math.max(currentPeak, abs);
        }
      }

      this.peak = Math.max(currentPeak, this.peak * this.smoothing);

      const targetPeak = 0.95;
      const gain = this.peak > 0 ? targetPeak / this.peak : 1;

      for (let channel = 0; channel < output.length; channel++) {
        const inputChannel = input[channel];
        const outputChannel = output[channel];

        for (let i = 0; i < inputChannel.length; i++) {
          outputChannel[i] = inputChannel[i] * gain;
        }
      }
    }

    return true;
  }
}

registerProcessor('audio-normalizer-processor', AudioNormalizerProcessor);
