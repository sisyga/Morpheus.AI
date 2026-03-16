# Miscellaneous Examples

Reference MorpheusML v4 XML models for miscellaneous simulations.

---

## FrenchFlag

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-FrenchFlag</Title>
        <Details>Wolpert L (1969). "Positional information and the spatial pattern of cellular differentiation". J. Theor. Biol. 25 (1): 1–47.</Details>
    </Description>
    <Global>
        <Field value="c_0*exp(-k/D*(l.x/size.x))" name="morphogen gradient" symbol="m">
            <Diffusion rate="0.0"/>
        </Field>
        <Constant value="1.0" symbol="c_0"/>
        <Constant value="0.75" symbol="D"/>
        <Constant value="1" symbol="k"/>
        <Constant value="0.0" symbol="celltype"/>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="20, 20, 0" symbol="size"/>
            <NodeLength value="1"/>
            <BoundaryConditions>
                <Condition boundary="x" type="constant"/>
                <Condition boundary="y" type="constant"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol name="location" symbol="l"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <Property value="0.0" name="p" symbol="p"/>
            <Property value="0.0" name="cell type" symbol="celltype"/>
            <Constant value="0.7" symbol="t1"/>
            <Constant value="0.4" symbol="t2"/>
            <Equation symbol-ref="celltype">
                <Expression>if(p>t1,3, if(p>t2, 2, 1))</Expression>
            </Equation>
            <Mapper name="report morphogen concentration">
                <Input value="m"/>
                <Output mapping="average" symbol-ref="p"/>
            </Mapper>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitCellLattice/>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="0">
            <Terminal name="png" persist="true"/>
            <Plot>
                <Cells value="celltype" opacity="0.5">
                    <ColorMap>
                        <Color value="3" color="blue"/>
                        <Color value="2" color="white"/>
                        <Color value="1" color="red"/>
                    </ColorMap>
                </Cells>
                <!--    <Disabled>
        <Field symbol-ref="m"/>
    </Disabled>
-->
            </Plot>
        </Gnuplotter>
        <Logger time-step="0.0">
            <Input>
                <Symbol symbol-ref="m"/>
                <Symbol symbol-ref="celltype"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Restriction>
                <Slice value="size.y/2" axis="y"/>
            </Restriction>
            <Plots>
                <Plot>
                    <Style style="linespoints"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="l.x"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="m"/>
                        <Symbol symbol-ref="celltype"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph format="svg" reduced="false" include-tags="#untagged"/>
    </Analysis>
</MorpheusModel>
```

## GameOfLife

```xml
<MorpheusModel version="4">
    <Description>Conway's Game of Life
---------------------

Classical Cellular Automaton with synchronized updates.


Rules:
- If alive, die when less than 2 live neighbors
- If alive, survive when 2 or 3 live neighbors (no change)
- If alive, die when more than 3 live neighbors
- If dead, become alive when exactly 3 live neighbors

<Title>Example-GameOfLife</Title>
        <Details>Simulates Conway's cellular automata model "Game of Life" by

1. summing the states of neighboring cells with NeighborhoodReporter
2. based on this sum, setting the cell state using a System of (synchronously updated) Rules.</Details>
    </Description>
    <Global>
        <Constant value="0" symbol="s"/>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="50, 50, 0" symbol="size"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="500"/>
        <SaveInterval value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType name="cell" class="biological">
            <Property value="0.0" name="State_Living" symbol="s"/>
            <Property value="0.0" name="Sum_Neighbors" symbol="sum"/>
            <System name="Rules of life" solver="Euler [fixed, O(1)]" time-step="1.0">
                <Rule symbol-ref="s">
                    <Expression>if((s == 1 and sum &lt;  2), 0,
  if((s == 1 and sum >  3), 0,
    if((s == 0 and sum == 3), 1, s)
  )
)
                    </Expression>
                </Rule>
            </System>
            <NeighborhoodReporter>
                <Input value="s" scaling="cell"/>
                <Output mapping="sum" symbol-ref="sum"/>
            </NeighborhoodReporter>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="0" type="cell">
            <InitProperty symbol-ref="s">
                <Expression>if(rand_uni(0,1) > 0.75, 1, 0)</Expression>
            </InitProperty>
            <InitCellLattice/>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter decorate="false" time-step="20">
            <Terminal name="png"/>
            <Plot>
                <Cells value="s">
                    <ColorMap>
                        <Color value="1" color="black"/>
                        <Color value="0.0" color="white"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <ModelGraph format="svg" reduced="false" include-tags="#untagged"/>
    </Analysis>
</MorpheusModel>
```

## GameOfLife_Global

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Details>This model shows:
- how to implement a simple cellular automata using a Global/Field.
- how to use NeighborhoodReporter to report on neighboring lattice sites within Fields.
</Details>
        <Title>Example-Game-of-Life-Field</Title>
    </Description>
    <Global>
        <Field value="if(rand_uni(0,1) > 0.75, 1, 0)" symbol="s">
            <Diffusion rate="0"/>
        </Field>
        <Field value="0" symbol="sum">
            <Diffusion rate="0.0"/>
        </Field>
        <System name="Rules of life" solver="Euler [fixed, O(1)]" time-step="1.0">
            <Rule symbol-ref="s">
                <Expression>if((s == 1 and sum >= w and sum &lt;= x ), 1,
if((s == 0 and sum >= y and sum &lt;= z ), 1, 0))
                    </Expression>
            </Rule>
            <Constant value="2" symbol="w"/>
            <Constant value="3" symbol="x"/>
            <Constant value="3" symbol="y"/>
            <Constant value="3" symbol="z"/>
        </System>
        <NeighborhoodReporter>
            <Input value="s"/>
            <Output mapping="sum" symbol-ref="sum"/>
        </NeighborhoodReporter>
    </Global>
    <Space>
        <Lattice class="square">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <Size value="200,200,0" symbol="size"/>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="1000"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Gnuplotter decorate="false" time-step="1">
            <Terminal name="png"/>
            <Plot>
                <Field symbol-ref="s">
                    <ColorMap>
                        <Color value="1" color="black"/>
                        <Color value="0.0" color="white"/>
                    </ColorMap>
                </Field>
            </Plot>
        </Gnuplotter>
        <ModelGraph format="svg" reduced="true" include-tags="#untagged"/>
    </Analysis>
</MorpheusModel>
```

## ParticleAggregation

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="3">
    <Description>
        <Title>Example-ParticleAggregation</Title>
        <Details>Shows new FlipCells plugin
</Details>
    </Description>
    <Global>
        <Variable symbol="sn" value="0" name="Sum of non-isolated cells"/>
        <Constant symbol="s" value="0"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size symbol="size" value="40, 40, 0"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
        </Lattice>
        <SpaceSymbol symbol="l"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="5000"/>
        <!--    <Disabled>
        <RandomSeed value="1415712648"/>
    </Disabled>
-->
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="spins">
            <Property symbol="s" value="0.0" name="state"/>
            <DelayProperty symbol="s_n" value="0.0" delay="1" name="state_neighbors"/>
            <Property symbol="p" value="2.25" name="probability"/>
            <Function symbol="ni" name="non-isolated">
                <Expression>if(s==1 and s_n > 1, 1, 0)</Expression>
            </Function>
            <NeighborhoodReporter>
                <Input scaling="cell" value="s"/>
                <Output symbol-ref="s_n" mapping="sum"/>
            </NeighborhoodReporter>
            <FlipCellMotion neighborhood="2" time-step="1">
                <Condition>s > 0 and rand_uni(0,1) &lt; (1-(s_n/12)*p)</Condition>
            </FlipCellMotion>
            <Mapper>
                <Input value="ni"/>
                <Output symbol-ref="sn" mapping="sum"/>
            </Mapper>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="0" type="spins">
            <InitProperty symbol-ref="s">
                <Expression>if(rand_uni(0,1) &lt; 0.10, 1, 0)</Expression>
            </InitProperty>
            <InitCellLattice/>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="100" decorate="false">
            <Terminal name="png"/>
            <Plot>
                <Cells value="s">
                    <ColorMap>
                        <Color value="1" color="black"/>
                        <Color value="0.0" color="white"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <Logger time-step="25">
            <Input>
                <Symbol symbol-ref="sn"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot time-step="250">
                    <Style style="lines" line-width="3.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="sn"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
    </Analysis>
</MorpheusModel>
```

## ShellCA

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-ShellCA</Title>
        <Details>This model implements Wolframs's rule 90 (https://en.wikipedia.org/wiki/Rule_90) generating Sierpinski triangles (https://en.wikipedia.org/wiki/Sierpinski_triangle).</Details>
    </Description>
    <Global>
        <Field value="if(space.x == 140 &#xa;or space.x == 141 &#xa;or space.x == 160 &#xa;or space.x == 161 &#xa;or space.x == 170 &#xa;or space.x == 171 , 1, 0)" symbol="state">
            <Diffusion rate="0.0"/>
        </Field>
        <Field value="0" symbol="n_state">
            <Diffusion rate="0.0"/>
        </Field>
        <NeighborhoodReporter>
            <Input value="state"/>
            <Output mapping="sum" symbol-ref="n_state"/>
        </NeighborhoodReporter>
        <System solver="Heun [fixed, O(2)]" time-step="1.0">
            <Rule symbol-ref="state">
                <Expression>(n_state)== 1</Expression>
            </Rule>
        </System>
    </Global>
    <Space>
        <Lattice class="linear">
            <Size value="500, 0, 0" symbol="size"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="250"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Logger time-step="1">
            <Input>
                <Symbol symbol-ref="state"/>
            </Input>
            <Output>
                <TextOutput file-format="matrix"/>
            </Output>
            <Plots>
                <SurfacePlot time-step="-1">
                    <Color-bar reverse-palette="true" palette="gray">
                        <Symbol symbol-ref="state"/>
                    </Color-bar>
                    <Terminal terminal="png"/>
                </SurfacePlot>
            </Plots>
        </Logger>
        <ModelGraph format="svg" reduced="false" include-tags="#untagged"/>
    </Analysis>
</MorpheusModel>
```
