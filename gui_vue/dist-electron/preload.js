"use strict";function i(e=["complete","interactive"]){return new Promise(t=>{e.includes(document.readyState)?t(!0):document.addEventListener("readystatechange",()=>{e.includes(document.readyState)&&t(!0)})})}const a={append(e,t){Array.from(e.children).find(o=>o===t)||e.appendChild(t)},remove(e,t){Array.from(e.children).find(o=>o===t)&&e.removeChild(t)}};function c(){const e="loaders-css__square-spin",t=`
@keyframes square-spin {
  0% {
    transform: rotate(0deg);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
  }
  25% { transform: perspective(100px) rotateX(180deg) rotateY(0);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
   }

  50% { transform: perspective(100px) rotateX(180deg) rotateY(180deg);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
  }
  75% { transform: perspective(100px) rotateX(0) rotateY(180deg);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
  }
  100% { transform: perspective(100px) rotateX(0) rotateY(0);
    background-image: url('icon_cube_border.png'); /* Replace with the URL of your image */
    background-size: cover; /* Scale the image to cover the entire container */
  }
}
.${e} > div {
  animation-fill-mode: both;
  width: 50px;
  height: 50px;
  background: #fff;
  animation: square-spin 3s 0s cubic-bezier(0.09, 0.57, 0.49, 0.9) infinite;
}
.app-loading-wrap {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #282c34;
  z-index: 99999;
}
    `,o=document.createElement("style"),r=document.createElement("div");return o.id="app-loading-style",o.innerHTML=t,r.className="app-loading-wrap",r.innerHTML=`<div class="${e}"><div></div></div>`,{appendLoading(){a.append(document.head,o),a.append(document.body,r)},removeLoading(){a.remove(document.head,o),a.remove(document.body,r)}}}const{appendLoading:d,removeLoading:n}=c();i().then(d);window.onmessage=e=>{e.data.payload==="removeLoading"&&n()};setTimeout(n,3e3);
