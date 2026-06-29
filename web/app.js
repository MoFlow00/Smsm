const RESULTS=document.getElementById("results");
const STATS=document.getElementById("stats");
const SEARCH=document.getElementById("search");

let manifest;

let currentPart=0;

let all=[];

async function start(){

    manifest=await fetch("../output/manifest.json").then(r=>r.json());

    STATS.innerHTML=`${manifest.total.toLocaleString()} Channels`;

    loadNext();
}

async function loadNext(){

    if(currentPart>=manifest.files.length)
        return;

    const file=manifest.files[currentPart];

    currentPart++;

    const rows=await fetch("../output/"+file).then(r=>r.json());

    all.push(...rows);

    render(rows);
}

function followers(v){

    if(v>=1000000)
        return (v/1000000).toFixed(1)+"M";

    if(v>=1000)
        return (v/1000).toFixed(1)+"K";

    return v;
}

function render(rows){

    rows.forEach(r=>{

        RESULTS.insertAdjacentHTML("beforeend",`

<div class="card">

<a
class="username"
target="_blank"
href="https://t.me/${r.username}">
@${r.username}
</a>

<div class="name">
${r.name}
</div>

<div class="info">

${followers(r.followers)}
&nbsp;&nbsp;

${r.type}

</div>

<div class="bio">

${r.bio}

</div>

</div>

`);

    });

}

window.addEventListener("scroll",()=>{

    if(window.innerHeight+window.scrollY>=document.body.offsetHeight-700){

        loadNext();

    }

});

SEARCH.addEventListener("input",()=>{

    const q=SEARCH.value.toLowerCase();

    RESULTS.innerHTML="";

    all
    .filter(x=>

        x.username.toLowerCase().includes(q) ||

        x.name.toLowerCase().includes(q)

    )
    .forEach(renderRow);

});

function renderRow(r){

RESULTS.insertAdjacentHTML("beforeend",`

<div class="card">

<a
class="username"
target="_blank"
href="https://t.me/${r.username}">
@${r.username}
</a>

<div class="name">
${r.name}
</div>

<div class="info">

${followers(r.followers)}
&nbsp;

${r.type}

</div>

<div class="bio">

${r.bio}

</div>

</div>

`);

}

start();
