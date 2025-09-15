## Making Prusa Core One great (and silent) again
- For fixing loudness on printing
- For fixing printing issues

### Tuning and calibration using firmware >= 6.4.0-alpha

#### Belt tuning
- If the printer is turned on, first disable the motors using ```Control->Disable motors``` in order not to break the hw board due to voltage overload

- Move the extruder to the center and the gantry to the back
- Start with loosening the belt completely
- Move the gantry to the front and let it bump to the front by moving forward and backward
- Make sure that the gantry is hitting both sides equally by listening
- If not, gently try to square the gantry by using a tool on the side that hits the front first and pull the gantry gently 
  on the other side until the gantry is hitting both sides equally 
- Tighten the belt tensioning screws equally (either use an allen key for that or a screwdriver with a marked side) until
  the belt are not loose anymore but slightly tensioned and does "sound like a bass guitar"
- Now run the ```Settings->Manual Belt Tuning``` wizard. Once it shows the frequency for the upper belt, try to tune the
  frequency 96 hz. Now tighten the belts equally until you see that the upper belt is "moving forward and backwards" in an optical way
  equally and slowly. Stay on the upper belt frequency but now tune the frequency until you see the lower belt is "moving forwards and backwards".
  If everything is perfect, you should be around 91 - 93 hz. If you see that the upper belt frequency is much lower than the lower belt frequency,
  it means that the gantry isn't square or you haven't tensioned the belt equally. Restart with step "loosening the belt completely".

#### Input shaper
- Grab/Buy the prusa [accelerometer](https://help.prusa3d.com/article/accelerometer-core-one-mk4-s-mk3-9-s_729349) ![accelerometer](https://cdn.help.prusa3d.com/wp-content/uploads/2025/04/410eb67ff568fddaa1019583b75ab776_painted.jpeg) 
- Open the back plug and lay the accelerometer at the back side of the sheet in order to make sure it won't be damaged by homing ![connection]({{site.baseurl}}/images/calibration.jpeg)
- Connect the accelerometer to the board ![picture](https://cdn.help.prusa3d.com/wp-content/uploads/2025/03/37cbb884af39165912f63c44aaa69454.jpg)
- Make sure the accelerometer isn't attached yet to the heatblock
- ```Settings->Input Shaper->Calibration ```, then press ```Continue```, the core one then will start homing
- If you have a sock on the heatblock, remove it
- Now attach the accelerometer ![accelerometer]({{site.baseurl}}/images/accelerometer.jpeg)
- Close the enclosure door and press ```Continue``` on the screen asking to "firmly attach the accelerometer".
- Calibration does start with x and then with y input shaper calibration
- Once it asks to "Store and use computed values" press ```Yes``` and you're done

#### Phase stepping
- Let the accelerometer connected
- Go to ```Return```, then being in the  ```Settings``` menu, select ```Phase Stepping->Calibration```, press ```Continue```
- Once calibration is done, it should list "Motor X/Y vibration reduced by xx%"
- Press ```OK``` and you're done


### Noise issues
#### Belt ripple sounds or metal ripping sounds when moving the gantry fast back and forth
1. Make sure that the belt is in the middle of the pulley gears, if not, move the gantry until you see
the pulley screw, loosen the pulley screw, place it gently up or down using a flat screwdriver in the right direction, then retighten the pulley and move the gantry 
to make sure it is perfectly centered.
![pulley]({{site.baseurl}}/images/pulley.png)
2. Make sure that the rods are slightly lubricated using sythetic grease (I recommend: Superlube 21030)

#### Noise when moving z-axis upwards/downwards
1. Auto home
2. Move the z-axis to the middle ```Control->Move Axis->Move Z``` to a value like 100mm
3. Loosen the screws and slowly retighten them in a crossing pattern
![screw]({{site.baseurl}}/images/screw.png)

#### Loudness on table
- Print the [hula](https://www.printables.com/model/873633-hula-v10-anti-vibration-feet-for-prusa-mk34-core-o) feet and the core one [connectors](https://www.printables.com/model/1288903-core-one-connector-for-hula)

#### Loudness on high speed printing in the night
- Use the stealth profile ```Settings->Stealth Mode``` to slow down fast movements

#### Belt tension not possible due to nut turning in tension idler
- Best print BEFORE this happens by replacing the tensioner pulley with [this version](https://www.printables.com/model/1360563-core-one-belt-tensioner-pulley-to-take-a-threaded/files)
  
### Printing issues

#### Residue at the nozzle when printing
- Residue on the nozzle when printing leading to print fails => In PrusaSlicer, set ```Printers, General, Size and coordinates -> Z offset``` to 0.1 mm
- If needed, reduce the Filament extrusion multiplier in PrusaSlicer ```Filaments, Filament -> Extrusion multiplier``` to a lower value, best print the calibration cube, see [here](https://help.prusa3d.com/article/extrusion-multiplier-calibration_2257) 

#### Issues at printing corners or at the edges / overhangs
- In PrusaSlicer, set ```Print Settings, Speed, Dynamic overhang speed -> speed for 75% overlap``` to a lower value such as 60%

#### Issues with infill lines being broken
- In PrusaSlicer set ```Print settings, Infill -> Fill pattern``` to Aligned Rectilinear or Gyroid

#### Print doesn't start if same project is modified and reprinted
- In PrusaSlicer ```Print Settings, Output options -> Output filename format``` add ```_{timestamp}```, for example ```{input_filename_base}_0.4n_{layer_height}mm_{printing_filament_types}_{printer_model}_{print_time}_{timestamp}.gcode```

#### My Print is taking too long
- In PrusaSlicer enable the option ```Print Settings, Infill, Reducing printing time -> Automatic infill combination```

Pictures (c) Prusa3d.com and (c) B.Kerler
