// Canonical project data shared by both portfolio experiences.
const GAMES = [
 {
  "title": "Kinder Easter",
  "wip": false,
  "cat": "ar",
  "section": "AR Games",
  "sub": "Made with Unity",
  "desc": "A Gameloft AR title — QR-scanned toys brought into the room through the camera. I built the main menu UI, the QR scanning and the AR toys. The build is under NDA; the video stands in for it.",
  "intro": "../images/kinder_intro.jpg",
  "info": "../images/kinder_info.jpg",
  "links": [
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=D22sO9HlWPY",
    "label": "Youtube"
   }
  ],
  "tags": [
   "Youtube"
  ]
 },
 {
  "title": "AAF",
  "wip": false,
  "cat": "ar",
  "section": "AR Games",
  "sub": "Made with Unity",
  "desc": "An AR title shipped at Gameloft: main menu UI, chat and gameplay work. Under NDA, so the video stands in for the build.",
  "intro": "../images/aaf_intro.jpg",
  "info": "../images/aaf_info.jpg",
  "links": [
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=SCXutaYWQdY",
    "label": "Youtube"
   }
  ],
  "tags": [
   "Youtube"
  ]
 },
 {
  "title": "AR demo",
  "wip": false,
  "cat": "ar",
  "section": "AR Games",
  "sub": "Made with Unity",
  "desc": "An ARFoundation sandbox — place a model on a real surface, walk around it, scale it. Built to learn the tracking rather than to ship.",
  "intro": "../images/game3_ar_demo_intro.jpg",
  "info": "../images/game3_ar_demo_info.jpg",
  "links": [
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=duy.ongoc.game3d_ar_survival",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/vSZhjpZjlmo",
    "label": "Youtube"
   }
  ],
  "tags": [
   "Android",
   "Youtube"
  ]
 },
 {
  "title": "Netcode Battle",
  "wip": false,
  "cat": "multiplayer",
  "section": "Multiplayer Games",
  "sub": "Made with Unity",
  "desc": "POLYGON Battle rebuilt as an online game: networked combat against real opponents instead of AI.",
  "intro": "../images/netcode_polygon_battle_intro.jpg",
  "info": "../images/netcode_polygon_battle_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_netcode_battle/",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=com.duyongoc.netcode.battle",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=yqIDxTWt-Lk&list=PLClQCm2rPi2VSzjd5MXOX40sx4GdrVJHk&index=36&ab_channel=duyongoc",
    "label": "Youtube"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=60D5mnJLUG8&list=PLClQCm2rPi2VSzjd5MXOX40sx4GdrVJHk&index=37&ab_channel=duyongoc",
    "label": "Youtube 2"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube"
  ]
 },
 {
  "title": "Netcode Shooter2D",
  "wip": false,
  "cat": "multiplayer",
  "section": "Multiplayer Games",
  "sub": "Made with Unity",
  "desc": "A 2D arena shooter over the network — movement, firing and hits kept in sync between clients.",
  "intro": "../images/netcode_shooter2d_intro.jpg",
  "info": "../images/netcode_shooter2d_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_netcode_shooter2d/",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=com.duyongoc.netcode.shooter2d",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=_tXlH7wFrgY&list=PLClQCm2rPi2VSzjd5MXOX40sx4GdrVJHk&index=38&ab_channel=duyongoc",
    "label": "Youtube"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=ZWL3WxXeSFg&list=PLClQCm2rPi2VSzjd5MXOX40sx4GdrVJHk&index=39&ab_channel=duyongoc",
    "label": "Youtube 2"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube"
  ]
 },
 {
  "title": "Netcode Demo",
  "wip": false,
  "cat": "multiplayer",
  "section": "Multiplayer Games",
  "sub": "Made with Unity",
  "desc": "A test bed for the netcode itself: several clients in one session with replicated state.",
  "intro": "../images/netcode_warrior_intro.png",
  "info": "../images/netcode_warrior_info.png",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_netcode_warrior/",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=com.duyongoc.netcode.warrior",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=gSs0tuP4IL0&list=PLClQCm2rPi2VSzjd5MXOX40sx4GdrVJHk&index=40&ab_channel=duyongoc",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube"
  ]
 },
 {
  "title": "Color Shoot 2d",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "A one-thumb colour-matching shooter. Written as a clean-architecture exercise — the source is public.",
  "intro": "../images/color_shoot_2d_intro.jpg",
  "info": "../images/color_shoot_2d_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_color_shoot",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=duy.ongoc.color_shooter",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=KEey_5kXaEY",
    "label": "Youtube"
   },
   {
    "kind": "Source",
    "url": "https://github.com/duyongoc/color_shoot2d",
    "label": "Source"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube",
   "Source"
  ]
 },
 {
  "title": "Math Game 2d",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "Timed arithmetic drills for kids. Same design-pattern exercise as the other two; the source is public.",
  "intro": "../images/MathGame2d_intro.png",
  "info": "../images/MathGame2d_info.png",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_math",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=duy.ongoc.math",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=OAwvB_e-t4g",
    "label": "Youtube"
   },
   {
    "kind": "Source",
    "url": "https://github.com/duyongoc/MathGame2d",
    "label": "Source"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube",
   "Source"
  ]
 },
 {
  "title": "Find Monkey 2d",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "A spot-the-difference memory game. Same design-pattern exercise; the source is public.",
  "intro": "../images/game2d_find_monkey_intro.jpg",
  "info": "../images/game2d_find_monkey_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_find_monkey",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=duy.ongoc.find_monkey",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=TnbUFuuK2Dw",
    "label": "Youtube"
   },
   {
    "kind": "Source",
    "url": "https://github.com/duyongoc/game2d_find_monkey",
    "label": "Source"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube",
   "Source"
  ]
 },
 {
  "title": "POLYGON Battle",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "Customize your character with a variety of skills and abilities, and team up against enemies.",
  "intro": "../images/polygon_battle_intro.jpg",
  "info": "../images/polygon_battle_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_POLYGON_Battle",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=com.duyongoc.polygon.battle",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=3GD8uI5WVa4&list=PLClQCm2rPi2VSzjd5MXOX40sx4GdrVJHk&index=34&ab_channel=duyongoc",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube"
  ]
 },
 {
  "title": "POLYGON Turnbase",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "Plan your formation carefully — unique abilities and a diverse array of units to outsmart your foes.",
  "intro": "../images/polygon_turnbase_intro.jpg",
  "info": "../images/polygon_turnbase_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_POLYGON_Turnbase",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=com.duyongoc.polygon.turnbase",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/i3wcBk7k2WA",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube"
  ]
 },
 {
  "title": "POLYGON Adventure",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "Join a courageous hero on a quest to save the world from an ancient evil.",
  "intro": "../images/polygon_adventure_intro.jpg",
  "info": "../images/polygon_adventure_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_POLYGON_Adventure",
    "label": "WebGL"
   },
   {
    "kind": "Android",
    "url": "https://play.google.com/store/apps/details?id=com.duyongoc.polygon.adventure",
    "label": "Android"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/P06ZWVtaAYM",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Android",
   "Youtube"
  ]
 },
 {
  "title": "Game Runner 3d",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "Run, avoid obstacles, destroy enemies and try to survive.",
  "intro": "../images/runner_template_intro.jpg",
  "info": "../images/runner_template_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_runner",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=Yp9mzhLPKZs",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Game Shooter 2d",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "Run, avoid obstacles, destroy enemies and try to survive. Run run run!",
  "intro": "../images/game2d_shooter_intro.jpg",
  "info": "../images/game2d_shooter_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_shooter",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=NOe_dEmwtL4",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Joust them all",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "Built with my team at the Gameloft 48h Game Jam 2021 — second place.",
  "intro": "../images/joust_them_all_intro.png",
  "info": "../images/joust_them_all_info.png",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_joust_them_all",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=UJL4NFY6-y8",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Cardgame Battle 2d",
  "wip": true,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "A turn-based card battler: build a deck, play a hand, trade blows.",
  "intro": "../images/game2d_battle_cardgame_intro.jpg",
  "info": "../images/game2d_battle_cardgame_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_battle_cardgame/",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/HKlnohqEyHY",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Battle Board 2d",
  "wip": true,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "Grid tactics — move units across a board and take ground one turn at a time.",
  "intro": "../images/game2d_battle_borad_intro.jpg",
  "info": "../images/game2d_battle_borad_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_battle_board/",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/xpw0TeMa0Z8",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Demo Dental 3d",
  "wip": false,
  "cat": "personal",
  "section": "MY GAMES",
  "sub": "Made with Unity",
  "desc": "A demo to customize and view a tooth model.",
  "intro": "../images/game3d_demo_teeth_intro.jpg",
  "info": "../images/game3d_demo_teeth_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_demo_teeth/",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/GCyKBid3mlg",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Subway Clone 3d",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "A Subway Surfers clone, built to match the original's feel — endless lane running.",
  "intro": "../images/game3d_subway_clone_intro.jpg",
  "info": "../images/game3d_subway_clone_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_subway_clone/",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/RL12SWwfVa4",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Topdown Sword",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "Top-down melee combat: dodge, close the distance, swing.",
  "intro": "../images/game3d_topdown_sword_intro.jpg",
  "info": "../images/game3d_topdown_sword_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_topdown_sword/",
    "label": "WebGL"
   }
  ],
  "tags": [
   "WebGL"
  ]
 },
 {
  "title": "Game3d Racing",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "A 3D arcade racer — steering, drift and lap timing.",
  "intro": "../images/game3d_racing_intro.jpg",
  "info": "../images/game3d_racing_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_racing/",
    "label": "WebGL"
   }
  ],
  "tags": [
   "WebGL"
  ]
 },
 {
  "title": "Survivor.io clone 2d",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "A Survivor.io clone: auto-attack, upgrade on level up, outlast the wave.",
  "intro": "../images/game2d_survivorIO_intro.jpg",
  "info": "../images/game2d_survivorIO_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_survivorIO_clone/",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/pv1M2DiOgu8",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Beat'em up",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "A side-scrolling brawler — combo strings and crowd control, stage by stage.",
  "intro": "../images/game2d5_beat_them_up_intro.jpg",
  "info": "../images/game2d5_beat_them_up_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": " https://webunity.github.io/webgl_game2d5_beat_them_up/",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/0wvAsGU9ahw",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Beat'em up 2",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "The brawler again, with heavier hit reactions and a new set of stages.",
  "intro": "../images/game2d5_beat_them_up_2_intro.jpg",
  "info": "../images/game2d5_beat_them_up_2_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": " https://webunity.github.io/webgl_game2d5_beat_them_up_2/",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://youtu.be/vxTd7zfsYsM",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Game2d Black Ops",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "A 2D run-and-gun: take cover, reload, clear the level.",
  "intro": "../images/game2d_metal_black_ops_intro.jpg",
  "info": "../images/game2d_metal_black_ops_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_metal_black_ops/",
    "label": "WebGL"
   }
  ],
  "tags": [
   "WebGL"
  ]
 },
 {
  "title": "Archer 2d",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "Tap and hold to draw. Hit as much fruit as you can.",
  "intro": "../images/archer2d_intro.jpg",
  "info": "../images/archer2d_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_archer",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=-sHI-cw3P8M",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Game Nightmares",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "Run away, avoid obstacles, try to survive.",
  "intro": "../images/game3d_nightmares_intro.jpg",
  "info": "../images/game3d_nightmares_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_nightmares",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=0LMDo26JBc4",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "City zombie",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "Find and kill other zombies. Become the Zombie King.",
  "intro": "../images/game3d_city_zombie_intro.jpg",
  "info": "../images/game3d_city_zombie_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_city_zombie",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=XLvpvH60OD0",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Topdown Shooter",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "A top-down survival shooter — kite the crowd and keep firing.",
  "intro": "../images/game3d_topdown_shooter_intro.jpg",
  "info": "../images/game3d_topdown_shooter_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_topdown_shooter",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=TB9RAgZCdWI",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Game 2d5 Dungeon",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "A 2.5D dungeon crawl: rooms, enemies, loot.",
  "intro": "../images/game2d5_dungeon_intro.jpg",
  "info": "../images/game2d5_dungeon_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d5_dungeon",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=GzRezjgOWBk",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Shoot ball 3d",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "Line up the shot and sink the ball.",
  "intro": "../images/game3d_shoot_ball_intro.png",
  "info": "../images/game3d_shoot_ball_info.png",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_shoot_ball",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=dcVBPY6tN5E",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Endless car 3d",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "An endless driver — dodge traffic and keep the run alive.",
  "intro": "../images/game3d_endless_car_intro.png",
  "info": "../images/game3d_endless_car_info.png",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game3d_endless_car",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=zOSg5cwtlLw",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 },
 {
  "title": "Jump 2d",
  "wip": false,
  "cat": "reskin",
  "section": "RESKIN",
  "sub": "Made with Unity",
  "desc": "Tap and hold to jump.",
  "intro": "../images/jump_2d_intro.jpg",
  "info": "../images/jump_2d_info.jpg",
  "links": [
   {
    "kind": "WebGL",
    "url": "https://webunity.github.io/webgl_game2d_jump",
    "label": "WebGL"
   },
   {
    "kind": "Youtube",
    "url": "https://www.youtube.com/watch?v=B38FsxEjxVM",
    "label": "Youtube"
   }
  ],
  "tags": [
   "WebGL",
   "Youtube"
  ]
 }
];
