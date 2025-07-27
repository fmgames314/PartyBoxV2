(function(){
  // ---------- helpers ----------
  function $(sel, root){ return (root||document).querySelector(sel); }
  function $all(sel, root){ return Array.from((root||document).querySelectorAll(sel)); }
  function hexToRgb(hex){
    const s = String(hex||"").replace("#","");
    if(s.length!==6) return [255,255,255];
    return [parseInt(s.slice(0,2),16), parseInt(s.slice(2,4),16), parseInt(s.slice(4,6),16)];
  }
  function rgbToHex(r,g,b){
    const h = (n)=>("0"+n.toString(16)).slice(-2);
    return "#"+h(r)+h(g)+h(b);
  }
  function clamp(v,lo,hi){ return Math.max(lo, Math.min(hi, v)); }

  // ---------- WS + state ----------
  const WS_STATUS = $("#ws-status");
  const FFT_CANVAS = $("#fftCanvas");
  const FFT_CTX = FFT_CANVAS ? FFT_CANVAS.getContext("2d") : null;

  const PREVIEW_CANVAS = $("#matrixPreview");
  const PREVIEW_CTX = PREVIEW_CANVAS ? PREVIEW_CANVAS.getContext("2d") : null;
  const PREVIEW_ROTATE = $("#preview-rotate");

  const MATRIX_W = 192, MATRIX_H = 32;

  let ws;
  let fftData = [];
  let fbImgData = null, fbW = 0, fbH = 0, lastFbAt = 0;
  const PREFER_SERVER_FB = true;

  // ---------- WS URL ----------
  const WS_URL = (() => {
    try{
      const u = new URL(window.location.href);
      const wsParam = u.searchParams.get("ws");
      if(wsParam) return wsParam;
    }catch(e){}
    const host = window.location.hostname || "127.0.0.1";
    return `ws://${host}:1997`;
  })();

  function wsSend(obj){
    try { if(ws && ws.readyState===1) ws.send(JSON.stringify(obj)); } catch(e){}
  }

  // Expose a few helpers for HTML handlers
  window.set_dsp_source = function(src){
    wsSend({event:"set_dsp_source", source: String(src||"")});
  };
  window.setSpotlight = function(group, index){
    wsSend({event:"set_spotlight", group: Number(group)||0, index: Number(index)||0});
  };

  // ---------- connect ----------
  function connectWS(){
    try{ ws = new WebSocket(WS_URL); }catch(e){
      WS_STATUS && (WS_STATUS.textContent = "failed to create websocket");
      return;
    }
    ws.onopen = ()=>{
      WS_STATUS && (WS_STATUS.textContent="connected");
      // identify as UI (safe no-op if server ignores)
      wsSend({event:"register_ui"});
      // get states
      wsSend({event:"get_panel_state"});
      wsSend({event:"get_miniDspState"});
    };
    ws.onclose = ()=>{
      WS_STATUS && (WS_STATUS.textContent="disconnected");
      setTimeout(connectWS, 1000);
    };
    ws.onerror = ()=>{
      WS_STATUS && (WS_STATUS.textContent="error");
    };
    ws.onmessage = (ev)=>{
      let pkt={}; try{ pkt=JSON.parse(ev.data); }catch(e){ return; }
      const name = pkt.event||"";
      if(name==="give_miniDspState"){
        if(pkt.DSP_preset!=null) $("#dsp-preset").textContent = pkt.DSP_preset;
        if(pkt.DSP_source!=null) $("#dsp-source").textContent = pkt.DSP_source;
        if(pkt.DSP_mute!=null) $("#dsp-mute").textContent = pkt.DSP_mute;
        if(pkt.DSP_volume!=null){
          $("#dsp-volume").value = pkt.DSP_volume;
          $("#dsp-volume-val").textContent = pkt.DSP_volume;
        }
        if(pkt.DSP_db_input) $("#dsp-in").textContent = JSON.stringify(pkt.DSP_db_input);
        if(pkt.DSP_db_output) $("#dsp-out").textContent = JSON.stringify(pkt.DSP_db_output);
      }
      else if(name==="give_panel_state"){
        // LEFT, CENTER, RIGHT objects
        ["LEFT","CENTER","RIGHT"].forEach(panel=>{
          const p = pkt[panel] || {};
          const root = document.querySelector(`.panel-controls[data-panel=${panel}]`);
          if(!root) return;
          // checkboxes
          ["option_blackBackground","option_emotexti","option_regularText","option_fft","option_fftCircles","option_clock"]
            .forEach(k=>{
              const el = root.querySelector(`input[type=checkbox][data-opt=${k}]`);
              if(el && (k in p)) el.checked = !!p[k];
            });
          // text fields
          const t = root.querySelector(`input[data-field=regularText_text]`);
          if(t && (p.regularText_text!=null)) t.value = p.regularText_text || "";
          const et = root.querySelector(`input[data-field=emotexti_text]`);
          if(et && (p.emotexti_text!=null)) et.value = p.emotexti_text || "";
          // scroll + speed
          const sc = root.querySelector(`input[type=checkbox][data-field=regularText_scroll]`);
          if(sc && (p.regularText_scroll!=null)) sc.checked = !!p.regularText_scroll;
          const sp = root.querySelector(`input[data-field=regularText_scrollSpeed]`);
          if(sp && (p.regularText_scrollSpeed!=null)) sp.value = p.regularText_scrollSpeed;
          // font size
          const fs = root.querySelector(`input[data-field=regularText_fontSize]`);
          if(fs && (p.regularText_fontSize!=null)) fs.value = p.regularText_fontSize;
          // FFT colors (expect arrays)
          const c1 = root.querySelector(`input[type=color][data-color=fft_color1]`);
          const c2 = root.querySelector(`input[type=color][data-color=fft_color2]`);
          if(Array.isArray(p.fft_color1) && c1) c1.value = rgbToHex(p.fft_color1[0]|0, p.fft_color1[1]|0, p.fft_color1[2]|0);
          if(Array.isArray(p.fft_color2) && c2) c2.value = rgbToHex(p.fft_color2[0]|0, p.fft_color2[1]|0, p.fft_color2[2]|0);
          // Regular text color might not be in panel_state yet; leave picker as-is.
        });
      }
      else if(name==="spectrum_data"){
        fftData = Array.isArray(pkt.data) ? pkt.data.slice() : [];
        drawSpectrumPreview();
      }
      else if(name==="framebuffer"){
        try{
          fbW = pkt.w|0; fbH = pkt.h|0;
          if(fbW===MATRIX_W && fbH===MATRIX_H && typeof pkt.data==="string"){
            const bstr = atob(pkt.data);
            const arr = new Uint8Array(bstr.length);
            for(let i=0;i<bstr.length;i++) arr[i] = bstr.charCodeAt(i)&255;
            fbImgData = arr; lastFbAt = performance.now();
          }
        }catch(e){}
      }
    };
  }
  connectWS();

  // ---------- controls -> WS ----------
  // Under lights
  const underColor = $("#under-color");
  const underFade  = $("#under-fade");
  if(underColor) underColor.addEventListener("input", e=>{
    wsSend({event:"set_setUnderRGBColor", color: e.target.value});
  });
  if(underFade) underFade.addEventListener("change", e=>{
    wsSend({event:"set_setUnderRGBFade", stat: e.target.checked?1:0});
  });

  // DSP volume
  const vol = $("#dsp-volume");
  if(vol) vol.addEventListener("input", e=>{
    const v = parseInt(e.target.value||"0",10);
    $("#dsp-volume-val").textContent = v;
    wsSend({event:"set_volume", volume:v});
  });

  // Panel controls
  $all(".panel-controls").forEach(root=>{
    const panel = root.getAttribute("data-panel");

    // options
    $all("input[type=checkbox][data-opt]", root).forEach(cb=>{
      cb.addEventListener("change", e=>{
        const option = e.target.getAttribute("data-opt");
        wsSend({event:"set_panel_option", panel, option, state: e.target.checked?1:0});
      });
    });

    // fields
    $all("input[data-field]", root).forEach(inp=>{
      const field = inp.getAttribute("data-field");
      if(field==="emotexti_text"){
        inp.addEventListener("change", e=>{
          wsSend({event:"set_emoji_text", panel, text: e.target.value||""});
        });
      }else if(field==="emotexti_fontSize"){
        inp.addEventListener("change", e=>{
          const size = parseInt(e.target.value||"0",10);
          wsSend({event:"set_emotexti_fontSize", panel, size});
        });
      }else if(field==="emotexti_backColor"){
        inp.addEventListener("input", e=>{
          wsSend({event:"set_emotexti_backColor", panel, color: e.target.value});
        });
      }else if(field==="emotexti_textColor"){
        inp.addEventListener("input", e=>{
          wsSend({event:"set_emotexti_textColor", panel, color: e.target.value});
        });
      }else if(field==="regularText_text"){
        inp.addEventListener("change", e=>{
          wsSend({event:"set_regularText_text", panel, text: e.target.value||""});
        });
      }else if(field==="regularText_scroll"){
        inp.addEventListener("change", e=>{
          wsSend({event:"set_regularText_scroll", panel, state: e.target.checked?1:0});
        });
      }else if(field==="regularText_scrollSpeed"){
        inp.addEventListener("change", e=>{
          const speed = parseFloat(e.target.value||"0")||0;
          wsSend({event:"set_regularText_scrollSpeed", panel, speed});
        });
      }else if(field==="regularText_fontSize"){
        inp.addEventListener("change", e=>{
          const size = parseInt(e.target.value||"0",10);
          wsSend({event:"set_regularText_fontSize", panel, size});
        });
      }else if(field==="regularText_color"){
        inp.addEventListener("input", e=>{
          wsSend({event:"set_regularText_color", panel, color: e.target.value});
        });
      }
    });

    // colors (fft)
    $all("input[type=color][data-color]", root).forEach(inp=>{
      const k = inp.getAttribute("data-color");
      inp.addEventListener("input", e=>{
        if(k==="fft_color1"){
          wsSend({event:"set_fft_color_1", panel, color: e.target.value});
        }else if(k==="fft_color2"){
          wsSend({event:"set_fft_color_2", panel, color: e.target.value});
        }
      });
    });
  });

  // ---------- Spectrum preview ----------
  function drawSpectrumPreview(){
    if(!FFT_CTX || !FFT_CANVAS) return;
    const W = FFT_CANVAS.width, H = FFT_CANVAS.height;
    FFT_CTX.clearRect(0,0,W,H);
    if(!fftData.length) return;
    const step = Math.max(1, Math.floor(fftData.length / W));
    for(let x=0,i=0; x<W; x++, i+=step){
      const v = fftData[Math.min(i, fftData.length-1)] || 0;
      const h = Math.round(clamp(v,0,31)/31 * H);
      FFT_CTX.fillStyle = "#00c8ff";
      FFT_CTX.fillRect(x, H-h, 1, h);
    }
  }

  // ---------- Live matrix preview ----------
  function blitServerFramebuffer(){
    if(!PREVIEW_CTX || !fbImgData) return false;
    try{
      const out = PREVIEW_CTX.createImageData(MATRIX_W, MATRIX_H);
      const od = out.data, rgb = fbImgData;
      let j=0;
      for(let i=0;i<rgb.length;i+=3){
        od[j++] = rgb[i];
        od[j++] = rgb[i+1];
        od[j++] = rgb[i+2];
        od[j++] = 255;
      }
      PREVIEW_CTX.putImageData(out, 0, 0);
      if(PREVIEW_ROTATE && PREVIEW_ROTATE.checked){
        // rotate 180
        const img = PREVIEW_CTX.getImageData(0,0,MATRIX_W,MATRIX_H);
        const data = img.data;
        const out2 = PREVIEW_CTX.createImageData(MATRIX_W, MATRIX_H);
        const od2 = out2.data;
        for(let y=0;y<MATRIX_H;y++){
          for(let x=0;x<MATRIX_W;x++){
            const si = (y*MATRIX_W + x)*4;
            const rx = MATRIX_W-1-x, ry = MATRIX_H-1-y;
            const di = (ry*MATRIX_W + rx)*4;
            od2[di]   = data[si];
            od2[di+1] = data[si+1];
            od2[di+2] = data[si+2];
            od2[di+3] = 255;
          }
        }
        PREVIEW_CTX.putImageData(out2, 0, 0);
      }
      return true;
    }catch(e){ return false; }
  }

  function render(){
    const now = performance.now();
    if(fbImgData && (now-lastFbAt)<300 && blitServerFramebuffer()){
      // drawn exact pixels
    }else{
      // keep canvas if no server frame; no-op (we rely on server frames)
    }
    requestAnimationFrame(render);
  }
  render();
})();
